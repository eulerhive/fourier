# Fourier

A Streamlit application for generating speech from text using Google Cloud Text-to-Speech API. This application provides a user-friendly web interface for converting text to speech with various language and voice options.

## About

Fourier is a project by [EulerHive](https://eulerhive.com) that provides advanced text-to-speech capabilities with a focus on quality and user experience.

## Features

- Text to speech conversion using Google Cloud TTS API
- Multiple language and voice selection
- Adjustable speech speed
- MP3 audio file generation and download
- Service account credential management
- Rate limiting to prevent abuse
- Mobile-responsive design

## Prerequisites

- Python 3.7+
- Google Cloud Platform account
- Service account with Text-to-Speech API access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/eulerhive/fourier.git
cd fourier
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
MAX_TEXT_LENGTH=5000
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60
CACHE_TTL=3600
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run src/app.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Upload your Google Cloud service account JSON file in the sidebar

4. Enter text, select language and voice options, and generate speech

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Cloud Text-to-Speech API
- Streamlit framework
- All contributors who have helped shape this project
- EulerHive team and community

## Security

Please report any security issues to [security@eulerhive.com](mailto:security@eulerhive.com)
