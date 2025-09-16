import json
import requests
import cloudlanguagetools.constants
import cloudlanguagetools.languages
import pinyin_jyutping


class MandarinCantoneseTransliteration(cloudlanguagetools.transliterationlanguage.TransliterationLanguage):
    def __init__(self, language, conversion_type, tone_numbers, spaces):
        self.service = cloudlanguagetools.constants.Service.MandarinCantonese
        self.service_fee = cloudlanguagetools.constants.ServiceFee.free
        self.language = language
        self.conversion_type = conversion_type
        self.tone_numbers = tone_numbers
        self.spaces = spaces

    def get_transliteration_name(self):
        conversion_type_str = self.conversion_type.capitalize()
        tone_numbers_str = "Diacritics"
        if self.tone_numbers:
            tone_numbers_str = "Tone Numbers"
        spaces_str = ""
        if self.spaces:
            spaces_str = "Spaces"
        return f'{self.language.lang_name} to {conversion_type_str} ({tone_numbers_str} {spaces_str}), {self.service.name}'

    def get_transliteration_shortname(self):
        conversion_type_str = self.conversion_type.capitalize()
        tone_numbers_str = "Diacritics"
        if self.tone_numbers:
            tone_numbers_str = "Tone Numbers"
        spaces_str = ""
        if self.spaces:
            spaces_str = "Spaces"
        return f'{conversion_type_str} ({tone_numbers_str} {spaces_str}), {self.service.name}'        

    def get_transliteration_key(self):
        return {
            'conversion_type': self.conversion_type,
            'tone_numbers': self.tone_numbers,
            'spaces': self.spaces
        }

class MandarinCantoneseService(cloudlanguagetools.service.Service):
    def __init__(self):
        self.pinyin_jyutping = pinyin_jyutping.PinyinJyutping()


    def get_tts_voice_list(self):
        return []

    def get_translation_language_list(self):
        return []

    def get_transliteration_language_list(self):
        result = []
        for tone_numbers in [True, False]:
            for spaces in [True, False]:
                result.append(MandarinCantoneseTransliteration(cloudlanguagetools.languages.Language.zh_cn, 'pinyin', tone_numbers, spaces))
                result.append(MandarinCantoneseTransliteration(cloudlanguagetools.languages.Language.zh_tw, 'pinyin', tone_numbers, spaces))
                result.append(MandarinCantoneseTransliteration(cloudlanguagetools.languages.Language.yue, 'jyutping', tone_numbers, spaces))
        return result

    def get_transliteration(self, text, transliteration_key):
        if transliteration_key['conversion_type'] == 'pinyin':
            return self.pinyin_jyutping.pinyin(text, tone_numbers=transliteration_key['tone_numbers'], spaces=transliteration_key['spaces'])
        elif transliteration_key['conversion_type'] == 'jyutping':
            return self.pinyin_jyutping.jyutping(text, tone_numbers=transliteration_key['tone_numbers'], spaces=transliteration_key['spaces'])

        raise Exception(f"unsupported conversion type: {transliteration_key['conversion_type']}")

    # full access, return all results
    def get_pinyin(self, text, tone_numbers, spaces, corrections):
        if len(corrections) == 0:
            return self.pinyin_jyutping.pinyin_all_solutions(text, tone_numbers, spaces)
        else:
            with_corrections = pinyin_jyutping.PinyinJyutping()
            with_corrections.load_pinyin_corrections(corrections)
            return with_corrections.pinyin_all_solutions(text, tone_numbers, spaces)

    def get_jyutping(self, text, tone_numbers, spaces, corrections):
        if len(corrections) == 0:
            return self.pinyin_jyutping.jyutping_all_solutions(text, tone_numbers, spaces)
        else:
            with_corrections = pinyin_jyutping.PinyinJyutping()
            with_corrections.load_jyutping_corrections(corrections)
            return with_corrections.jyutping_all_solutions(text, tone_numbers, spaces)