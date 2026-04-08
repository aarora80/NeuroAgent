# Neurology Clinic Intake Bot

A conversational AI assistant for neurology clinic patient intake and triage, built with Pipecat, OpenAI, and ElevenLabs TTS.

## Overview

This bot automates the neurology clinic intake process by:
- Collecting patient demographics and medical history
- Systematically screening for neurological symptoms
- Checking for red-flag symptoms that require immediate attention
- Determining appropriate neurology subspecialty based on symptoms
- Generating EMR summaries for clinical documentation
- Providing scheduling recommendations

## Features

### 🎯 **Conversational Interface**
- Natural voice interaction using ElevenLabs TTS
- Real-time speech recognition and transcription
- Empathetic, professional medical communication style

### 📋 **Comprehensive Triage**
- **Demographics Collection**: Name, DOB, contact info, insurance, referring physician
- **Symptom Screening**: 11 systematic neurological symptom categories
- **Red Flag Detection**: Immediate emergency symptom identification
- **Follow-up Questions**: Detailed symptom assessment for positive responses

### 🧠 **Intelligent Subspecialty Matching**
- Automatic subspecialty recommendation based on symptoms
- Supports: Headache, Seizure, Movement Disorders, Cognitive/Memory, Vision, Speech, Spine, Sleep, Dizziness, General Neurology

### 📊 **EMR Integration**
- Automatic generation of clinical summaries
- JSON export for EMR system integration
- Patient data tracking and documentation
- Incomplete conversation handling

### 🔄 **Call Management**
- Automatic EMR summary generation on call termination
- Participant leave/room end event handling
- Idle timeout management
- Conversation state tracking

## Installation

### Prerequisites
- Python 3.8+
- Daily.co account for video calls
- OpenAI API key
- ElevenLabs API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd patient-intake-standalone
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` with your API keys:
   ```
   OPENAI_API_KEY=your_openai_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_key_here
   ```

4. **Install sound assets**
   - Ensure the `assets/` directory contains the required sound files
   - Sound files are used for UI feedback during conversations

## Usage

### Running the Bot

1. **Start the server**
   ```bash
   python server.py
   ```

2. **Join the Daily.co room**
   - The bot will automatically join and wait for participants
   - Use the provided room URL to connect

3. **Begin the intake process**
   - The bot will introduce itself and start collecting patient information
   - Follow the conversational flow to complete the triage

### Testing Without Voice

For development and testing without using voice credits:

```bash
python bot.py --url <daily-room-url> --token <daily-room-token>
```

## Architecture

### Core Components

- **`bot.py`**: Main bot logic and conversation flow
- **`server.py`**: Daily.co integration and call management
- **`emr_plugin.py`**: EMR summary generation and export
- **`neurology_triage_schema.py`**: Medical triage questions and flow
- **`neurology_subspecialty_keywords.py`**: Subspecialty matching logic

### Conversation Flow

1. **Introduction** → Bot introduces itself and explains the process
2. **Demographics** → Collects patient basic information
3. **Symptom Screening** → Systematic symptom assessment one-by-one
4. **Red Flag Checking** → Emergency symptom evaluation
5. **Follow-up Questions** → Detailed symptom assessment
6. **Subspecialty Determination** → AI-powered specialty matching
7. **EMR Summary** → Clinical documentation generation
8. **Scheduling Recommendation** → Next steps and appointment guidance

### Data Flow

```
Patient Voice → Speech Recognition → LLM Processing → 
TTS Response → EMR Summary → JSON Export
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM | Yes |
| `ELEVENLABS_API_KEY` | ElevenLabs API key for TTS | Yes |

### Customization

- **Voice**: Change `voice_id` in `bot.py` for different TTS voices
- **Symptoms**: Modify `neurology_triage_schema.py` for different symptom sets
- **Subspecialties**: Update `neurology_subspecialty_keywords.py` for custom matching

## Troubleshooting

### Common Issues

1. **"No module named 'pipecat'"**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

2. **"API key not found"**
   - Check your `.env` file has the correct API keys
   - Verify environment variables are loaded

3. **"Daily room connection failed"**
   - Verify room URL and token are correct
   - Check Daily.co room permissions

4. **"TTS not working"**
   - Verify ElevenLabs API key is valid
   - Check voice ID exists in your ElevenLabs account

### Debug Mode

Enable debug logging by uncommenting the logger configuration in `bot.py`:

```python
logger.add(sys.stderr, level="DEBUG")
```

## Development

### Adding New Symptoms

1. Edit `neurology_triage_schema.py`
2. Add symptom key, question, and follow-up questions
3. Update red flag mapping in `bot.py` if needed

### Modifying Subspecialty Logic

1. Edit `neurology_subspecialty_keywords.py`
2. Add new keywords and subspecialty mappings
3. Test with various symptom combinations

### EMR Integration

The bot generates JSON summaries compatible with most EMR systems:

```json
{
  "patient_info": {...},
  "symptoms": {...},
  "red_flags": [...],
  "recommended_subspecialty": "...",
  "timestamp": "..."
}
```

## Version History

### Iteration 1
- ✅ Basic conversation flow with demographics collection
- ✅ Systematic symptom screening with red flag detection
- ✅ Subspecialty determination based on symptoms
- ✅ EMR summary generation and export
- ✅ Call termination handling and cleanup
- ✅ ElevenLabs TTS integration
- ✅ Daily.co video call integration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the debug logs
- Open an issue on GitHub

---

**Note**: This bot is designed for clinical use and should be tested thoroughly before deployment in a medical setting. Always ensure compliance with local healthcare regulations and data privacy laws.
