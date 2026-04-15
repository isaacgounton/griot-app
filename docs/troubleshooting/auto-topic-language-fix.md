# Auto Topic Language Selection Fix

## Issue Description

When using the auto topic feature on the content creation dashboard (https://griotpevi.com/dashboard/content-creation), the language selection was not being applied correctly. Videos would always be generated in English regardless of the selected language.

## Root Cause

The issue was caused by a mismatch between language code formats used in different parts of the system:

- **Frontend**: Sends language codes like 'en', 'fr', 'es' 
- **Script Generator**: Expects full language names like 'english', 'french', 'spanish'
- **TTS Service**: Expects language codes like 'en', 'fr', 'es'

When auto topic was enabled, the language code was passed directly to the script generator without being mapped to the expected format.

## Solution

Added language code to language name mapping in all video generation pipelines:

### Files Modified

1. **app/services/ai/unified_video_pipeline.py**
   - Added `_map_language_code_to_name()` method
   - Maps language codes for script generation while keeping original codes for TTS

2. **app/services/ai/footage_to_video_pipeline.py** 
   - Added same language mapping method
   - Updated script generation calls to use mapped language names
   - Updated topic discovery calls to use language codes

3. **app/services/ai/aiimage_to_video_pipeline.py**
   - Added same language mapping method
   - Updated script and topic discovery calls

4. **app/routes/ai/script_generation.py**
   - Added inline language mapping for direct API calls

### Language Mapping

```python
language_mapping = {
    'en': 'english',
    'fr': 'french', 
    'es': 'spanish',
    'de': 'german',
    'it': 'italian',
    'pt': 'portuguese',
    'ru': 'russian',
    'zh': 'chinese',
    'ja': 'japanese',
    'ko': 'korean',
    'ar': 'arabic',
    'hi': 'hindi',
    'th': 'thai',
    'vi': 'vietnamese',
    'pl': 'polish',
    'nl': 'dutch',
    # ... and more
}
```

## How It Works Now

1. **Frontend** sends language code (e.g., 'fr') 
2. **Topic Discovery** uses language code for trend research
3. **Script Generation** receives mapped language name ('french')
4. **TTS Service** receives original language code ('fr')

## Testing

The fix has been verified to:

- ✅ Correctly map language codes to language names
- ✅ Generate scripts in the selected language 
- ✅ Preserve language codes for TTS services
- ✅ Work with all auto topic script types

## Usage

Users can now:

1. Go to https://griotpevi.com/dashboard/content-creation
2. Enable auto topic discovery
3. Select any supported language
4. Generate videos that will be in the selected language

The system will automatically:
- Find trending topics relevant to the selected language/region
- Generate scripts in the selected language
- Use appropriate voices for the selected language
- Create videos with the correct language throughout

## Supported Languages

The fix supports 25+ languages including:
- English (en)
- French (fr) 
- Spanish (es)
- German (de)
- Italian (it)
- Portuguese (pt)
- Russian (ru)
- Chinese (zh)
- Japanese (ja)
- Korean (ko)
- Arabic (ar)
- And more...
