// Language detection utility for topic text
// Uses common words and patterns to detect the most likely language

interface LanguagePattern {
  code: string;
  name: string;
  commonWords: string[];
  patterns: RegExp[];
  weight: number;
}

const LANGUAGE_PATTERNS: LanguagePattern[] = [
  {
    code: 'en',
    name: 'English',
    commonWords: ['the', 'and', 'is', 'in', 'it', 'you', 'that', 'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'i', 'at', 'be', 'this', 'have', 'from', 'or', 'one', 'had', 'by', 'word', 'but', 'not', 'what', 'all', 'were', 'we', 'when', 'your', 'can', 'said', 'there', 'each', 'which', 'she', 'do', 'how', 'their', 'if', 'will', 'up', 'other', 'about', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like', 'into', 'him', 'has', 'two', 'more', 'go', 'no', 'way', 'could', 'my', 'than', 'first', 'been', 'call', 'who', 'oil', 'its', 'now', 'find', 'long', 'down', 'day', 'did', 'get', 'come', 'made', 'may', 'part'],
    patterns: [/\b(the|and|is|in|it|you|that|he|was|for|on|are|as|with|his|they)\b/gi],
    weight: 1
  },
  {
    code: 'es',
    name: 'Spanish',
    commonWords: ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'como', 'pero', 'sus', 'me', 'ya', 'muy', 'sin', 'sobre', 'ser', 'tiene', 'todo', 'esta', 'también', 'hasta', 'hay', 'donde', 'han', 'quien', 'están', 'estado', 'desde', 'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos', 'qué', 'unos', 'yo', 'otro', 'otras', 'otra', 'él', 'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada', 'muchos', 'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo', 'nosotros', 'mi', 'mis', 'tú', 'te', 'ti', 'tu', 'tus', 'ellas', 'nosotras', 'vosotros', 'vosotras', 'os', 'mío', 'mía', 'míos', 'mías'],
    patterns: [/\b(el|la|de|que|y|en|un|es|se|no|te|lo|le|da|su|por|son|con|para|al|del|los|las|una|como|pero|sus|me|ya|muy|sin|sobre|ser|tiene|todo|esta|también|hasta|hay|donde|han|quien|están|estado|desde)\b/gi],
    weight: 1
  },
  {
    code: 'fr',
    name: 'French',
    commonWords: ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour', 'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus', 'par', 'grand', 'en', 'une', 'être', 'et', 'en', 'avoir', 'que', 'pour', 'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus', 'par', 'grand', 'en', 'une', 'être', 'et', 'en', 'avoir', 'que', 'pour', 'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus', 'par', 'grand', 'en', 'une'],
    patterns: [/\b(le|la|les|de|du|des|et|à|un|une|il|elle|être|avoir|que|pour|dans|ce|cette|son|sa|ses|sur|avec|ne|se|pas|tout|tous|toute|toutes|plus|par|grand|grande|grands|grandes|en)\b/gi],
    weight: 1
  },
  {
    code: 'de',
    name: 'German',
    commonWords: ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für', 'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als', 'auch', 'es', 'an', 'werden', 'aus', 'er', 'hat', 'dass', 'sie', 'nach', 'wird', 'bei', 'einer', 'um', 'am', 'sind', 'noch', 'wie', 'einem', 'über', 'einen', 'so', 'zum', 'war', 'haben', 'nur', 'oder', 'aber', 'vor', 'zur', 'bis', 'mehr', 'durch', 'man', 'sein', 'wurde', 'sei', 'in'],
    patterns: [/\b(der|die|das|und|in|den|von|zu|mit|sich|des|auf|für|ist|im|dem|nicht|ein|eine|als|auch|es|an|werden|aus|er|hat|dass|sie|nach|wird|bei|einer|um|am|sind|noch|wie|einem|über|einen|so|zum|war|haben|nur|oder|aber|vor|zur|bis|mehr|durch|man|sein|wurde|sei)\b/gi],
    weight: 1
  },
  {
    code: 'it',
    name: 'Italian',
    commonWords: ['il', 'di', 'che', 'e', 'la', 'per', 'un', 'in', 'con', 'del', 'da', 'a', 'al', 'delle', 'dei', 'nel', 'su', 'le', 'si', 'una', 'o', 'anche', 'lo', 'ma', 'se', 'ci', 'questo', 'come', 'gli', 'tutto', 'sono', 'una', 'tra', 'della', 'fatto', 'quando', 'molto', 'ci', 'senza', 'essere', 'cose', 'queste', 'dove', 'quello', 'me', 'dopo', 'quanto', 'quelli', 'fare', 'loro', 'qui', 'così', 'prima', 'stata', 'quanta', 'altro', 'lui', 'nel', 'noi', 'mio', 'tempo', 'lei', 'dire', 'ogni', 'sua', 'quale', 'cosa', 'tanto', 'lavoro', 'grande', 'stato', 'bene', 'gruppo', 'stesso', 'paese', 'casa', 'caso', 'parte', 'durante', 'nuovo', 'anni', 'possibile', 'più'],
    patterns: [/\b(il|di|che|e|la|per|un|in|con|del|da|a|al|delle|dei|nel|su|le|si|una|o|anche|lo|ma|se|ci|questo|come|gli|tutto|sono|una|tra|della|fatto|quando|molto|ci|senza|essere|cose|queste|dove|quello|me|dopo|quanto|quelli|fare|loro|qui|così|prima|stata|quanta|altro|lui|nel|noi|mio|tempo|lei|dire|ogni|sua|quale|cosa|tanto|lavoro|grande|stato|bene|gruppo|stesso|paese|casa|caso|parte|durante|nuovo|anni|possibile|più)\b/gi],
    weight: 1
  },
  {
    code: 'pt',
    name: 'Portuguese',
    commonWords: ['o', 'a', 'de', 'e', 'do', 'da', 'em', 'um', 'para', 'é', 'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos', 'como', 'mas', 'foi', 'ao', 'ele', 'das', 'tem', 'à', 'seu', 'sua', 'ou', 'ser', 'quando', 'muito', 'há', 'nos', 'já', 'está', 'eu', 'também', 'só', 'pelo', 'pela', 'até', 'isso', 'ela', 'entre', 'era', 'depois', 'sem', 'mesmo', 'aos', 'ter', 'seus', 'suas', 'numa', 'pelos', 'pelas', 'esse', 'eles', 'tinha', 'foram', 'essa', 'num', 'nem', 'suas', 'meu', 'às', 'minha', 'têm', 'numa', 'pelos', 'pelas', 'essas', 'esses', 'pelas', 'pelos', 'sobre', 'entre', 'durante', 'antes', 'deles', 'delas', 'dele', 'dela', 'nós', 'vocês', 'eles', 'elas'],
    patterns: [/\b(o|a|de|e|do|da|em|um|para|é|com|não|uma|os|no|se|na|por|mais|as|dos|como|mas|foi|ao|ele|das|tem|à|seu|sua|ou|ser|quando|muito|há|nos|já|está|eu|também|só|pelo|pela|até|isso|ela|entre|era|depois|sem|mesmo|aos|ter|seus|suas|numa|pelos|pelas|esse|eles|tinha|foram|essa|num|nem|suas|meu|às|minha|têm)\b/gi],
    weight: 1
  },
  {
    code: 'ru',
    name: 'Russian',
    commonWords: ['в', 'и', 'не', 'на', 'я', 'быть', 'тот', 'он', 'оно', 'она', 'они', 'с', 'а', 'как', 'по', 'это', 'все', 'к', 'из', 'у', 'который', 'мы', 'этот', 'один', 'но', 'да', 'его', 'для', 'что', 'ты', 'за', 'её', 'если', 'уже', 'или', 'ни', 'быть', 'было', 'только', 'себя', 'свой', 'мой', 'до', 'такой', 'здесь', 'чтобы', 'где', 'много', 'более', 'после', 'конечно', 'может', 'наш', 'лучше', 'очень', 'жить', 'вы', 'во', 'через', 'раз', 'тут', 'при', 'без', 'так', 'года', 'жизни', 'будет', 'нет', 'под'],
    patterns: [/[а-яё]/gi],
    weight: 2
  },
  {
    code: 'ja',
    name: 'Japanese',
    commonWords: ['の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'し', 'れ', 'さ', 'ある', 'いる', 'も', 'する', 'から', 'な', 'こと', 'として', 'い', 'や', 'れる', 'など', 'なっ', 'ない', 'この', 'ため', 'その', 'あっ', 'よう', 'また', 'もの', 'という', 'あり', 'まで', 'られ', 'なる', 'へ', 'か', 'だ', 'これ', 'によって', 'により', 'おり', 'より', 'による', 'ず', 'なり', 'られる', 'において', 'ば', 'なかっ', 'なく', 'しかし', 'について', 'せ', 'だっ', 'その後', 'できる', 'それ'],
    patterns: [/[ひらがな]|[カタカナ]|[漢字]/gi, /[あ-ん]|[ア-ン]|[一-龯]/gi],
    weight: 3
  },
  {
    code: 'ko',
    name: 'Korean',
    commonWords: ['이', '그', '저', '것', '들', '에', '는', '을', '를', '과', '와', '의', '로', '으로', '에서', '까지', '부터', '에게', '께', '한테', '보다', '처럼', '같이', '마다', '조차', '까지도', '밖에', '뿐', '만', '도', '라도', '나마', '이라도', '든지', '거나', '이든지', '던지', '이던지'],
    patterns: [/[가-힣]/gi],
    weight: 3
  },
  {
    code: 'zh',
    name: 'Chinese',
    commonWords: ['的', '一', '是', '在', '不', '了', '有', '和', '人', '这', '中', '大', '为', '上', '个', '国', '我', '以', '要', '他', '时', '来', '用', '们', '生', '到', '作', '地', '于', '出', '就', '分', '对', '成', '会', '可', '主', '发', '年', '动', '同', '工', '也', '能', '下', '过', '子', '说', '产', '种', '面', '而', '方', '后', '多', '定', '行', '学', '法', '所', '民', '得', '经', '十', '三', '之', '进', '着', '等', '部', '度', '家', '电', '力', '里', '如', '水', '化', '高', '自', '二', '理', '起', '小', '物', '现', '实', '加', '量', '都', '两', '可以'],
    patterns: [/[一-龯]/gi],
    weight: 3
  }
];

export function detectLanguage(text: string): string {
  if (!text || text.trim().length === 0) {
    return 'en'; // Default to English for empty text
  }

  const normalizedText = text.toLowerCase();
  const scores: { [key: string]: number } = {};

  // Initialize scores
  LANGUAGE_PATTERNS.forEach(lang => {
    scores[lang.code] = 0;
  });

  // Score based on common words
  LANGUAGE_PATTERNS.forEach(lang => {
    lang.commonWords.forEach(word => {
      const regex = new RegExp(`\\b${word}\\b`, 'gi');
      const matches = normalizedText.match(regex);
      if (matches) {
        scores[lang.code] += matches.length * lang.weight;
      }
    });

    // Score based on patterns (for non-Latin scripts)
    lang.patterns.forEach(pattern => {
      const matches = text.match(pattern);
      if (matches) {
        scores[lang.code] += matches.length * lang.weight * 2; // Higher weight for character patterns
      }
    });
  });

  // Find the language with the highest score
  let maxScore = 0;
  let detectedLang = 'en';

  Object.entries(scores).forEach(([langCode, score]) => {
    if (score > maxScore) {
      maxScore = score;
      detectedLang = langCode;
    }
  });

  // If no language scored points, default to English
  return maxScore > 0 ? detectedLang : 'en';
}

export function getLanguageName(languageCode: string): string {
  const lang = LANGUAGE_PATTERNS.find(l => l.code === languageCode);
  return lang ? lang.name : 'English';
}

export function getSupportedLanguages(): Array<{ code: string; name: string }> {
  return LANGUAGE_PATTERNS.map(lang => ({
    code: lang.code,
    name: lang.name
  }));
}