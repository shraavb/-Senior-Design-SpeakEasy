# Catalan Subtitle Sources for Dataset Expansion

## Recommended Subtitle Download Sites

### Primary Sources (Catalan Subtitles Available)

1. **OpenSubtitles** - https://www.opensubtitles.org
   - 5+ million subtitles in 50+ languages including Catalan
   - Free downloads in SRT format
   - API available for bulk downloads

2. **Podnapisi.net** - https://www.podnapisi.net
   - 2.1+ million subtitles, 101 languages
   - Set preferred language filter for Catalan

3. **Subscene** - https://subscene.com
   - 60+ languages including Catalan
   - Daily updates with new films

4. **Subdl** - https://subdl.com
   - 100+ languages including Catalan
   - Ad-free interface

## Recommended Catalan TV Series (Rich in Slang)

### Must-Have Series for Youth/Colloquial Language

| Series | Year | Platform | Why It's Good |
|--------|------|----------|---------------|
| **Merlí** | 2015-2018 | Netflix, TV3, Prime | Barcelona high school setting, youth slang, philosophy discussions |
| **Polseres Vermelles** | 2011-2013 | TV3 | Teen drama, hospital setting, emotional vocabulary |
| **El cor de la ciutat** | 2000-2009 | TV3 | Barcelona soap opera, everyday conversations |
| **Cites** | 2015-2017 | TV3 | Dating show format, romantic/social slang |
| **Ventdelplà** | 2005-2010 | TV3 | Rural Catalonia, family dynamics |
| **La Riera** | 2010-2017 | TV3 | Coastal town drama, diverse characters |

### Netflix Spanish Series (Barcelona-Based)

| Series | Year | Notes |
|--------|------|-------|
| **Hache** | 2019-2021 | 1960s Barcelona, crime drama |
| **Mano de Hierro** | 2024 | Barcelona port, drug trafficking |
| **Hasta el cielo: La serie** | 2023 | Barcelona heist crew |

### Films with Barcelona/Catalan Content

| Film | Year | Slang Level |
|------|------|-------------|
| Barcelona Summer Night | 2013 | High - youth party culture |
| Spanish Affair 1 & 2 | 2014, 2015 | Medium - Catalan/Basque clash |
| Tres dies amb la família | 2009 | Medium - family dynamics |
| A Gun in Each Hand | 2012 | High - Barcelona men's struggles |
| Catalunya über alles | 2011 | Medium - Catalan identity |

## TV3 Direct Access

**TV3 a la carta**: https://www.3cat.cat/3cat/
- Official Catalan broadcaster
- Most content has Catalan subtitles built-in
- Free access to recent episodes

## Bulk Download Strategy

### Using OpenSubtitles API
```python
# Example API query for Catalan subtitles
import requests

params = {
    'sublanguageid': 'cat',  # Catalan language code
    'query': 'merli',
    'format': 'json'
}
# API endpoint: https://api.opensubtitles.com/
```

### Priority Download List

**High Priority (Most Slang):**
1. Merlí (all seasons) - ~40 episodes
2. Barcelona Summer Night (2013)
3. Spanish Affair 1 & 2
4. Tres dies amb la família

**Medium Priority:**
5. Polseres Vermelles (all seasons)
6. A Gun in Each Hand
7. Vicky Cristina Barcelona (additional versions)
8. El cor de la ciutat (selected episodes)

## Language Codes Reference

| Site | Catalan Code |
|------|--------------|
| OpenSubtitles | `cat` |
| Podnapisi | `ca` |
| Subscene | `Catalan` |
| ISO 639-1 | `ca` |

## Notes

- Focus on content from 2010-2024 for current slang
- Youth-oriented content (Merlí, Polseres) has more colloquial language
- TV3 productions are the most authentic for Barcelona Catalan
- Netflix Spanish content is dubbed/subtitled but less authentic for regional slang
