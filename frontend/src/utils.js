export function weatherEmoji(description) {
  if (!description) return '🌡️'
  const d = description.toLowerCase()
  if (d.includes('thunder')) return '⛈️'
  if (d.includes('heavy snow') || d.includes('blizzard')) return '🌨️'
  if (d.includes('snow') || d.includes('sleet') || d.includes('ice pellet')) return '❄️'
  if (d.includes('heavy rain') || d.includes('violent') || d.includes('torrential')) return '🌧️'
  if (d.includes('rain') || d.includes('drizzle') || d.includes('shower')) return '🌦️'
  if (d.includes('fog') || d.includes('mist') || d.includes('haze') || d.includes('rime')) return '🌫️'
  if (d.includes('overcast')) return '☁️'
  if (d.includes('partly') || d.includes('cloudy') || d.includes('cloud') || d.includes('broken')) return '⛅'
  if (d.includes('clear') || d.includes('sunny') || d.includes('mainly clear')) return '☀️'
  if (d.includes('wind')) return '💨'
  return '🌡️'
}

// Returns CSS glow color for icon based on weather
export function iconGlow(description) {
  const d = (description || '').toLowerCase()
  if (d.includes('thunder')) return 'rgba(180,100,255,0.5)'
  if (d.includes('snow') || d.includes('blizzard')) return 'rgba(180,220,255,0.5)'
  if (d.includes('rain') || d.includes('drizzle') || d.includes('shower')) return 'rgba(80,140,220,0.5)'
  if (d.includes('fog') || d.includes('mist')) return 'rgba(180,180,200,0.3)'
  if (d.includes('cloud') || d.includes('overcast')) return 'rgba(140,160,200,0.3)'
  return 'rgba(255,170,60,0.55)'   // sunny
}

// Top radial warm glow behind the icon
export function topGlow(description) {
  const d = (description || '').toLowerCase()
  if (d.includes('thunder')) return 'rgba(100,50,200,0.18)'
  if (d.includes('snow') || d.includes('blizzard')) return 'rgba(100,160,240,0.18)'
  if (d.includes('rain') || d.includes('drizzle') || d.includes('shower')) return 'rgba(50,100,200,0.18)'
  if (d.includes('fog') || d.includes('mist')) return 'rgba(120,120,160,0.15)'
  if (d.includes('cloud') || d.includes('overcast')) return 'rgba(100,120,180,0.18)'
  return 'rgba(220,110,30,0.22)'   // sunny warm
}

export function splitLocation(locationName) {
  if (!locationName) return { city: 'Unknown', country: '' }
  const parts = locationName.split(', ')
  if (parts.length === 1) return { city: parts[0], country: '' }
  return { city: parts[0], country: parts[parts.length - 1] }
}

export function formatDay(dateStr) {
  const d = new Date(dateStr + 'T12:00:00')
  const isToday = dateStr === new Date().toISOString().slice(0, 10)
  if (isToday) return 'Today'
  return d.toLocaleDateString('en-US', { weekday: 'short' })
}

export function formatFullDate(dateStr) {
  return new Date(dateStr + 'T12:00:00').toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric',
  })
}

export function round(val) {
  if (val === null || val === undefined) return '—'
  return Math.round(val)
}

// Human-friendly weather descriptions
const DESC_MAP = [
  [['thunder'],                       'Thunderstorms Rolling In'],
  [['blizzard', 'heavy snow'],        'Heavy Snow Falling'],
  [['snow grains'],                   'Light Flurries'],
  [['slight snow'],                   'Just a Dusting of Snow'],
  [['snow'],                          'Snowy Outside'],
  [['sleet', 'ice pellet'],           'Watch Out — Icy!'],
  [['violent', 'torrential'],         'Pouring Rain'],
  [['heavy rain'],                    'Heavy Rain'],
  [['moderate rain'],                 'Steady Rain'],
  [['slight rain', 'light rain'],     'A Little Rainy'],
  [['dense drizzle', 'heavy drizzle'],'Drizzling Out There'],
  [['drizzle'],                       'Light Drizzle'],
  [['rain shower', 'shower'],         'Scattered Showers'],
  [['rain'],                          'Rainy Day'],
  [['depositing rime', 'dense fog'],  'Very Foggy'],
  [['fog', 'mist', 'haze'],           'Foggy & Misty'],
  [['overcast'],                      'Gray Skies All Day'],
  [['partly cloudy', 'partly'],       'Partly Cloudy'],
  [['mainly clear'],                  'Mostly Sunny'],
  [['clear sky', 'clear', 'sunny'],   'Beautiful & Sunny'],
  [['cloudy', 'cloud', 'broken'],     'Cloudy Skies'],
]

export function humanDescription(desc) {
  if (!desc) return ''
  const d = desc.toLowerCase()
  for (const [keywords, label] of DESC_MAP) {
    if (keywords.some(k => d.includes(k))) return label
  }
  return desc
}

// Human-friendly UV index
export function uvLabel(uv) {
  if (uv === null || uv === undefined) return null
  const v = Math.round(uv)
  if (v <= 2)  return { label: 'No sunscreen needed', color: '#4caf50',  icon: '😎' }
  if (v <= 5)  return { label: 'Wear sunscreen outside', color: '#cddc39', icon: '🌤️' }
  if (v <= 7)  return { label: 'Hat + SPF 30 recommended', color: '#ffc107', icon: '☀️' }
  if (v <= 10) return { label: 'Limit time in direct sun', color: '#ff5722', icon: '🥵' }
  return       { label: 'Avoid going out at midday', color: '#e53935',  icon: '🔥' }
}

// Human-friendly AQI info
export const AQI_HUMAN = {
  1: { label: 'Go Outside!',    detail: 'Air is as clean as it gets',        color: '#4caf50' },
  2: { label: "Air's Good",     detail: 'Nothing to worry about today',      color: '#8bc34a' },
  3: { label: 'A Bit Iffy',     detail: 'Might bother you if you have asthma', color: '#ffc107' },
  4: { label: 'Not Great Out',  detail: 'Try to stay inside when you can',   color: '#ff5722' },
  5: { label: 'Stay In!',       detail: 'Air outside can make you feel sick', color: '#e53935' },
}
