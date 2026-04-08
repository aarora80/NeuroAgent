import asyncio
import os
import sys
import wave

import aiohttp
from dotenv import load_dotenv
from loguru import logger
from openai import OpenAI
from runner import configure

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import OutputAudioRawFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContextFrame
from pipecat.processors.frame_processor import FrameDirection
from pipecat.processors.logger import FrameLogger
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.openai.llm import OpenAILLMContext, OpenAILLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport

# Import the neurology triage schema
from neurology_triage_schema import DEMO_QUESTIONS, SYMPTOM_FLOW, RED_FLAG_KEYWORDS, SUBSPECIALTY_MAP
from neurology_subspecialty_keywords import SUBSPECIALTY_KEYWORDS, SUBSPECIALTY_INFO, SUBSPECIALTY_MAPPING
from emr_plugin import EMRPlugin

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="INFO")

sounds = {}
sound_files = [
    "clack-short.wav",
    "clack.wav",
    "clack-short-quiet.wav",
    "ding.wav",
    "ding2.wav",
]

script_dir = os.path.dirname(__file__)

for file in sound_files:
    # Build the full path to the sound file
    full_path = os.path.join(script_dir, "assets", file)
    # Get the filename without the extension to use as the dictionary key
    filename = os.path.splitext(os.path.basename(full_path))[0]
    # Open the sound and convert it to bytes
    with wave.open(full_path) as audio_file:
        sounds[file] = OutputAudioRawFrame(
            audio_file.readframes(-1), audio_file.getframerate(), audio_file.getnchannels()
        )


class IntakeProcessor:
    def __init__(self, context: OpenAILLMContext):
        # Build schema and triage guidance for the LLM
        lines = []

        # Role & Overall Task
        lines.append("You are a neurology clinic intake assistant. Your role is to guide the patient through a structured, empathetic conversation to fill out a neurology triage form. Speak like a professional clinician—friendly, patient, and precise.")

        # Gating Logic
        lines.append("IMPORTANT: You must complete all demographic fields FIRST before beginning symptom screening. Do NOT ask about or call any symptom-related function (like screen_symptoms) until all demographic fields are collected and you call collect_patient_info.")

        # Demographics Phase
        lines.append("\n--- DEMOGRAPHIC INFO TO COLLECT ---")
        lines.append("Ask these questions one at a time. After each answer, repeat or paraphrase what you heard, then move on. Do NOT ask 'is that correct?' after every answer—just let the user correct you if needed.")
        for key, question in DEMO_QUESTIONS:
            lines.append(f"- {key}: {question}")
        lines.append("Once all demographic fields are collected (name, DOB, contact, insurance, referring physician, reason for visit, symptom onset, urgency), call the collect_patient_info function. This will automatically begin the symptom triage phase.")

        # Symptom Triage Phase
        lines.append("\n--- SYMPTOM SCREENING FLOW ---")
        lines.append("Ask about ONE symptom at a time.")
        lines.append("For EVERY symptom, always ask the main yes/no question, even if the reason for visit matches that symptom. If the reason for visit matches, acknowledge it (e.g., 'I know you mentioned headaches as your main concern...'), but still confirm with a yes/no question for that symptom.")
        lines.append("If patient answers 'yes', ask each follow-up question for that symptom ONE BY ONE. Wait for the answer to each before moving on.")
        lines.append("If 'no', move on to the next symptom. Do NOT group or batch questions.")
        lines.append("IMPORTANT: For every answer to a symptom or follow-up question, call the screen_symptoms function with the user's response as the argument. Do not proceed to the next question without calling the function.")
        for key, question, followups in SYMPTOM_FLOW:
            lines.append(f"- {key}: {question}")
            if followups:
                for f in followups:
                    lines.append(f"    * Follow-up: {f}")

        # Red Flags
        lines.append("\n--- RED FLAG KEYWORDS ---")
        for k, v in RED_FLAG_KEYWORDS.items():
            lines.append(f"- '{k}': {v}")
        lines.append("If a red flag is detected, calmly advise the patient to seek urgent care. Then continue with the intake.")

        # Subspecialty Mapping
        lines.append("\n--- SUBSPECIALTY KEYWORDS ---")
        for k, v in SUBSPECIALTY_KEYWORDS.items():
            lines.append(f"- '{k}': {v}")

        # General Rules & Voice
        lines.append("\n--- TRIAGE INSTRUCTIONS ---")
        lines.append("1. Speak like a human clinician, not a script. Be conversational and empathetic.")
        lines.append("2. Ask one question at a time. Confirm or repeat answers when appropriate.")
        lines.append("3. Wait for the patient's answer before continuing. Never ask multiple questions at once.")
        lines.append("4. After each function call, continue naturally—acknowledge the answer and move on.")
        lines.append("5. Use follow-ups when the answer to a symptom is 'yes'. Ask each follow-up individually.")
        lines.append("6. Do not begin symptom questions until collect_patient_info has been called.")
        lines.append("7. At the end, thank the patient, ask if they’d like to add anything, and say that the team will review the info and schedule their visit.")
        lines.append("8. Do not call any function after symptoms are done. The system will auto-generate the summary.")

        # Flow control recap
        lines.append("\n--- FLOW SUMMARY ---")
        lines.append("Step 1: Complete demographics (call collect_patient_info only once all fields are gathered).")
        lines.append("Step 2: Begin symptom screening, one symptom at a time, using follow-ups if needed.")
        lines.append("Step 3: Detect red flags and advise care if necessary, but continue intake.")
        lines.append("Step 4: After all symptoms are collected, use the collected answers to determine the most appropriate neurology subspecialty for the patient. Finish by closing the conversation respectfully.")
        lines.append("Do not trigger any more functions after subspecialty is determined.")

        # Final system message build
        system_prompt = "\n".join(lines)
        context.add_message({
            "role": "system",
            "content": system_prompt
        })
        context.set_tools([
            {
                "type": "function",
                "function": {
                    "name": "collect_patient_info",
                    "description": "Collects patient demographics and intake info.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "dob": {"type": "string"},
                            "contact": {"type": "string"},
                            "insurance": {"type": "string"},
                            "referring_physician": {"type": "string"},
                            "reason_for_visit": {"type": "string"},
                            "symptom_onset": {"type": "string"},
                            "urgency": {"type": "string", "enum": ["Routine", "Urgent", "Emergency"]},
                        },
                    },
                },
            }
        ])

    # Red flag questions for each symptom (matching the actual form)
    RED_FLAG_MAP = {}  # No hardcoded map anymore

    def is_yes(self, resp: str) -> bool:
        """Check if response indicates yes"""
        if not resp:
            return False
        resp_lower = resp.lower().strip()
        yes_words = ["yes", "yeah", "yep", "yup", "sure", "okay", "ok", "correct", "right", "true", "1", "one"]
        return any(word in resp_lower for word in yes_words)

    def is_no(self, resp: str) -> bool:
        """Check if response indicates no"""
        if not resp:
            return False
        resp_lower = resp.lower().strip()
        no_words = ["no", "nope", "nah", "not", "negative", "false", "0", "zero", "none", "never"]
        return any(word in resp_lower for word in no_words)

    async def llm_determine_subspecialty(self, context):
        """
        Use the LLM to determine the most appropriate neurology subspecialty based on symptoms and demographics.
        """
        logger.info("DEBUG: Starting LLM subspecialty determination...")
        
        # Prepare patient data
        demographics = getattr(context, 'patient_demographics', {})
        symptoms = getattr(context, 'symptom_answers', {})
        red_flags = getattr(context, 'red_flags', [])
        
        logger.info(f"DEBUG: Demographics: {demographics}")
        logger.info(f"DEBUG: Symptoms: {symptoms}")
        logger.info(f"DEBUG: Red flags: {red_flags}")
        
        # Build patient summary
        summary_lines = [
            "PATIENT SUMMARY:",
            f"- Reason for visit: {demographics.get('reason_for_visit', 'Not specified')}",
            f"- Urgency: {demographics.get('urgency', 'Routine')}",
            "\nPOSITIVE SYMPTOMS:"
        ]
        
        # Add positive symptoms
        for key, data in symptoms.items():
            if data.get('yes', False):
                symptom_name = key.replace('_', ' ').title()
                summary_lines.append(f"- {symptom_name}")
                followups = data.get('followups', [])
                for f in followups:
                    summary_lines.append(f"  * {f}")
        
        if red_flags:
            summary_lines.append("\nRED FLAGS:")
            for flag in red_flags:
                summary_lines.append(f"- {flag}")
        
        # Add available subspecialties as reference
        summary_lines.append("\nAVAILABLE SUBSPECIALTIES:")
        for subspecialty_info in SUBSPECIALTY_MAPPING:
            subspecialty_name = subspecialty_info["subspecialty"]
            aliases = subspecialty_info["aliases"]
            common_symptoms = subspecialty_info["common_symptoms"]
            summary_lines.append(f"- {subspecialty_name}")
            if aliases:
                summary_lines.append(f"  Aliases: {', '.join(aliases)}")
            summary_lines.append(f"  Common cases: {common_symptoms}")
            summary_lines.append("")
        
        summary_lines.append("INSTRUCTIONS:")
        summary_lines.append("1. Choose the most specific subspecialty based on symptoms")
        summary_lines.append("2. If unclear or multiple options, choose 'General Neurology'")
        summary_lines.append("3. Reply with ONLY the subspecialty name")
        summary_lines.append("")
        summary_lines.append("Which subspecialty is most appropriate?")
        
        prompt = "\n".join(summary_lines)
        logger.info(f"DEBUG: LLM prompt:\n{prompt}")
        
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=20,
                temperature=0
            )
            subspecialty = response.choices[0].message.content.strip()
            logger.info(f"DEBUG: LLM response: '{subspecialty}'")
            
            # Validate against known subspecialties
            valid_subspecialties = [info["subspecialty"] for info in SUBSPECIALTY_MAPPING]
            if subspecialty not in valid_subspecialties:
                logger.info(f"DEBUG: Invalid subspecialty '{subspecialty}', defaulting to General Neurology")
                return "General Neurology"
            
            return subspecialty
            
        except Exception as e:
            logger.error(f"DEBUG: Error calling LLM for subspecialty determination: {e}")
            return "General Neurology"

    async def collect_patient_info(self, params: FunctionCallParams):
        # Store all demographics in context for EMR
        if params.arguments:
            params.context.patient_demographics = {
                "name": params.arguments.get("name", "Unknown"),
                "dob": params.arguments.get("dob", "Unknown"),
                "contact": params.arguments.get("contact", "Not provided"),
                "insurance": params.arguments.get("insurance", "Not provided"),
                "referring_physician": params.arguments.get("referring_physician", "Not specified"),
                "reason_for_visit": params.arguments.get("reason_for_visit", "Not specified"),
                "symptom_onset": params.arguments.get("symptom_onset", "Not specified"),
                "urgency": params.arguments.get("urgency", "Routine")
            }
            params.context.reason_for_visit = params.arguments.get("reason_for_visit", "")
        
        # After collecting demographics, move to symptom screening
        await params.result_callback([
            {"role": "system", "content": "Thank you for providing your information. Now, I'll ask about specific symptoms one by one. Please answer yes or no to each, and I'll ask follow-up questions if needed."}
        ])
        
        # Initialize symptom screening
        params.context.symptom_index = 0
        params.context.symptom_answers = {}
        params.context.followup_index = 0
        params.context.in_followup = False
        params.context.red_flags = []
        
        # Start with first symptom
        symptom_flow = SYMPTOM_FLOW
        if symptom_flow:
            first_key, first_question, _ = symptom_flow[0]
            await params.result_callback([
                {"role": "system", "content": first_question}
            ])
        
        # Update tools to include symptom screening
        params.context.set_tools([
            {
                "type": "function",
                "function": {
                    "name": "screen_symptoms",
                    "description": "Screen symptoms one by one with red flag checking.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_response": {"type": "string"},
                        },
                    },
                },
            }
        ])

    async def screen_symptoms(self, params: FunctionCallParams):
        """
        Screen symptoms with integrated red flag checking as first follow-up.
        If user says 'yes' to a symptom, ask follow-ups (first is red flag if present).
        If any follow-up (red flag) is answered 'yes', note the red flag and set urgency to urgent.
        """
        # Gating: Ensure demographics are collected first
        if not hasattr(params.context, 'patient_demographics'):
            await params.result_callback([
                {"role": "system", "content": "Let’s complete your basic information first before discussing symptoms. Can I confirm your name and date of birth?"}
            ])
            return
        symptom_flow = SYMPTOM_FLOW
        if not hasattr(params.context, "symptom_index"):
            params.context.symptom_index = 0
            params.context.symptom_answers = {}
            params.context.followup_index = 0
            params.context.in_followup = False
            params.context.red_flags = []
        idx = params.context.symptom_index
        followup_idx = params.context.followup_index
        in_followup = params.context.in_followup
        answers = params.context.symptom_answers
        # Check if we're done with all symptoms
        if idx >= len(symptom_flow):
            print(">>> ✅ Exiting symptom screening, moving to subspecialty selection")
            logger.info("✅ All symptoms collected. Triggering scheduling decision...")
            # Call determine_scheduling directly with the context
            result = await self.determine_scheduling_direct(params.context)
            await params.result_callback(result)
            return
        symptom_key, question, followups = symptom_flow[idx]
        # Use new SYMPTOM_FLOW format: last follow-up is red flag (tuple), others are strings
        symptom_followups = list(followups)
        if not symptom_followups:
            symptom_followups = ["Are the symptoms rapidly worsening?"]
        # Ensure last follow-up is a (question, red_flag_key) tuple
        if not isinstance(symptom_followups[-1], tuple):
            symptom_followups[-1] = (symptom_followups[-1], "rapidly_worsening")
        red_flag_question, red_flag_key = symptom_followups[-1]
        # Get user response
        user_response = ""
        if params.arguments and "user_response" in params.arguments:
            user_response = params.arguments.get("user_response", "")
        elif params.context.messages and len(params.context.messages) > 0:
            last_message = params.context.messages[-1]
            if last_message.get("role") == "user":
                user_response = last_message.get("content", "")
        logger.info(f"DEBUG: screen_symptoms called - idx={idx}, in_followup={in_followup}")
        logger.info(f"DEBUG: Current symptom: {symptom_key} - {question}")
        logger.info(f"DEBUG: user_response='{user_response}'")
        # Main symptom question
        if not in_followup:
            if self.is_yes(user_response):
                # Always record as present immediately
                answers[symptom_key] = {"yes": True, "followups": []}
                params.context.in_followup = True
                params.context.followup_index = 0
                # Ask first follow-up (string or tuple)
                first_followup = symptom_followups[0]
                if isinstance(first_followup, tuple):
                    first_followup = first_followup[0]
                await params.result_callback([
                    {"role": "system", "content": first_followup}
                ])
                return
            elif self.is_no(user_response):
                answers[symptom_key] = {"yes": False}
                idx += 1
                params.context.symptom_index = idx
                if idx >= len(symptom_flow):
                    print(">>> ✅ Exiting symptom screening, moving to subspecialty selection")
                    logger.info("✅ All symptoms collected. Triggering scheduling decision...")
                    # Call determine_scheduling directly with the context
                    result = await self.determine_scheduling_direct(params.context)
                    await params.result_callback(result)
                    return
                else:
                    next_key, next_question, _ = symptom_flow[idx]
                    await params.result_callback([
                        {"role": "system", "content": next_question}
                    ])
                    return
            else:
                await params.result_callback([
                    {"role": "system", "content": f"I'm sorry, could you please answer yes or no? {question}"}
                ])
                return
        # Follow-up questions (including red flag as first follow-up)
        if in_followup:
            if symptom_key not in answers:
                answers[symptom_key] = {"yes": True, "followups": []}
            # For follow-ups, check if this is the red flag (last follow-up)
            is_red_flag = followup_idx == len(symptom_followups) - 1
            # If tuple, extract question for storage
            followup_q = symptom_followups[followup_idx]
            if isinstance(followup_q, tuple):
                followup_q = followup_q[0]
            answers[symptom_key]["followups"].append(user_response)
            # If this is the red flag follow-up and user says yes, note red flag and set urgency
            if is_red_flag and self.is_yes(user_response):
                params.context.red_flags.append(f"Red flag for {symptom_key}")
                if hasattr(params.context, 'patient_demographics'):
                    params.context.patient_demographics['urgency'] = 'Urgent'
            followup_idx += 1
            if followup_idx < len(symptom_followups):
                params.context.followup_index = followup_idx
                next_followup = symptom_followups[followup_idx]
                if isinstance(next_followup, tuple):
                    next_followup = next_followup[0]
                await params.result_callback([
                    {"role": "system", "content": next_followup}
                ])
                return
            else:
                params.context.in_followup = False
                params.context.followup_index = 0
                idx += 1
                params.context.symptom_index = idx
                if idx >= len(symptom_flow):
                    print(">>> ✅ Exiting symptom screening, moving to subspecialty selection")
                    logger.info("✅ All symptoms collected. Triggering scheduling decision...")
                    # Call determine_scheduling directly with the context
                    result = await self.determine_scheduling_direct(params.context)
                    await params.result_callback(result)
                    return
                else:
                    next_key, next_question, _ = symptom_flow[idx]
                    await params.result_callback([
                        {"role": "system", "content": next_question}
                    ])
                    return

    async def determine_scheduling(self, params: FunctionCallParams):
        print(">>> ✅ Determining scheduling")
        # Gating: Ensure symptoms are collected first
        if not hasattr(params.context, 'symptom_answers') or not params.context.symptom_answers:
            logger.warning("Tried to determine scheduling before symptoms collected.")
            return
        # Use the LLM to determine the appropriate subspecialty
        subspecialty = await self.llm_determine_subspecialty(params.context)
        params.context.recommended_subspecialty = subspecialty
        # Generate EMR summary first
        await self._generate_emr_summary(params.context)
        # Create a more detailed summary with subspecialty information
        summary = (
            f"Thank you for completing the neurology intake screening. "
            f"Based on your symptoms, I recommend scheduling with our {subspecialty} specialist. "
            f"Our team will review your information and contact you through your referring physician "
            f"to schedule your appointment. If you have any questions, please don't hesitate to reach out. "
            f"Have a great day!"
        )
        return [{"role": "system", "content": summary}]

    async def determine_scheduling_direct(self, context):
        """Helper to call determine_scheduling logic with just context, for internal use."""
        # Use the same logic as determine_scheduling, but with context only
        if not hasattr(context, 'symptom_answers') or not context.symptom_answers:
            logger.warning("Tried to determine scheduling before symptoms collected.")
            return
        subspecialty = await self.llm_determine_subspecialty(context)
        context.recommended_subspecialty = subspecialty
        await self._generate_emr_summary(context)
        summary = (
            f"Thank you for completing the neurology intake screening. "
            f"Based on your symptoms, I recommend scheduling with our {subspecialty} specialist. "
            f"Our team will review your information and contact you through your referring physician "
            f"to schedule your appointment. If you have any questions, please don't hesitate to reach out. "
            f"Have a great day!"
        )
        return [{"role": "system", "content": summary}]

    async def _generate_emr_summary(self, context):
        """Generate EMR summary from conversation data"""
        try:
            plugin = EMRPlugin()
            
            # Pass the recommended subspecialty to the plugin
            if hasattr(context, 'recommended_subspecialty'):
                plugin.recommended_subspecialty = context.recommended_subspecialty
            
            # Extract conversation data from context
            conversation_data = self._extract_conversation_data(context)
            
            # Process conversation and generate summary
            triage_summary = plugin.process_conversation(conversation_data)
            
            # Print summary to console
            plugin.print_summary(triage_summary)
            
            # Export to JSON file
            filename = plugin.export_to_json(triage_summary)
            
            print(f"\n✅ EMR Summary generated: {filename}")
            
        except Exception as e:
            print(f"❌ Error generating EMR summary: {e}")

    def _extract_conversation_data(self, context) -> str:
        """Extract conversation data from context for EMR processing"""
        # Extract patient demographics and symptom data from context
        data = {
            "demographics": getattr(context, 'patient_demographics', {}),
            "symptoms": {},
            "red_flags": getattr(context, 'red_flags', []),
            "recommended_subspecialty": getattr(context, 'recommended_subspecialty', 'General Neurology')
        }
        
        # Extract symptom answers
        if hasattr(context, 'symptom_answers'):
            data["symptoms"] = context.symptom_answers
        
        print(f"DEBUG: Extracted conversation data: {data}")
        
        # Convert to string for processing
        return str(data)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", type=str, help="Daily room URL")
    parser.add_argument("-t", "--token", type=str, help="Daily room token")
    args = parser.parse_args()
    
    async with aiohttp.ClientSession() as session:
        if args.url and args.token:
            room_url = args.url
            token = args.token
        else:
            (room_url, token) = await configure(session)

        transport = DailyTransport(
            room_url,
            token,
            "Chatbot",
            DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                transcription_enabled=True,
                #
                # Spanish
                #
                # transcription_settings=DailyTranscriptionSettings(
                #     language="es",
                #     tier="nova",
                #     model="2-general"
                # )
            ),
        )

        tts = ElevenLabsTTSService(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice_id="Wq15xSaY3gWvazBRaGEU",  # Nathaniel - medical-neutral
            zero_retention=True
        )

        llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

        messages = []
        context = OpenAILLMContext(messages=messages)
        context_aggregator = llm.create_context_aggregator(context)

        intake = IntakeProcessor(context)
        llm.register_function("collect_patient_info", intake.collect_patient_info)
        llm.register_function("screen_symptoms", intake.screen_symptoms)
        llm.register_function("determine_scheduling", intake.determine_scheduling)

        fl = FrameLogger("LLM Output")

        pipeline = Pipeline(
            [
                transport.input(),  # Transport input
                context_aggregator.user(),  # User responses
                llm,  # LLM
                fl,  # Frame logger
                tts,  # TTS
                transport.output(),  # Transport output
                context_aggregator.assistant(),  # Assistant responses
            ]
        )

        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
        )

        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            await transport.capture_participant_transcription(participant["id"])
            print("DEBUG: First participant joined, starting conversation...")
            # Mark conversation as started
            context.conversation_started = True
            context.participant_id = participant["id"]
            await task.queue_frames([OpenAILLMContextFrame(context)])

        @transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, *args):
            """Handle when participant leaves the call"""
            print(f"Participant {participant['id']} left the call")
            
            # Generate EMR summary if conversation was started and has data
            if (hasattr(context, 'conversation_started') and context.conversation_started and 
                hasattr(context, 'symptom_answers') and context.symptom_answers):
                print("Generating EMR summary due to participant leaving...")
                await intake._generate_emr_summary(context)
            elif hasattr(context, 'conversation_started') and context.conversation_started:
                print("Conversation started but no symptom data collected - generating minimal summary")
                await intake._generate_emr_summary(context)
            
            # Clean up
            print("Call ended - cleaning up resources")

        @transport.event_handler("on_room_ended")
        async def on_room_ended(transport):
            """Handle when the room ends"""
            print("Room ended - generating final EMR summary")
            
            # Generate EMR summary if conversation was started
            if (hasattr(context, 'conversation_started') and context.conversation_started and 
                hasattr(context, 'symptom_answers') and context.symptom_answers):
                await intake._generate_emr_summary(context)
            elif hasattr(context, 'conversation_started') and context.conversation_started:
                print("Conversation started but no symptom data collected - generating minimal summary")
                await intake._generate_emr_summary(context)
            
            print("Room cleanup completed")

        # Add timeout handler for idle conversations
        @transport.event_handler("on_idle_timeout")
        async def on_idle_timeout(transport):
            """Handle when conversation is idle for too long"""
            print("Idle timeout detected - generating EMR summary")
            
            if (hasattr(context, 'conversation_started') and context.conversation_started and 
                hasattr(context, 'symptom_answers') and context.symptom_answers):
                await intake._generate_emr_summary(context)
            elif hasattr(context, 'conversation_started') and context.conversation_started:
                await intake._generate_emr_summary(context)
            
            print("Idle timeout cleanup completed")

        runner = PipelineRunner()

        await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())