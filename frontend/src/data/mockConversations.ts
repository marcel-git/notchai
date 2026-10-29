import type { Conversation, Suggestion } from '../types/chat'

export const mockConversations: Conversation[] = [
  {
    id: 'mock-1',
    title: 'The art of subtle persuasion',
    character_id: null,
    persona_id: null,
    messages: [
      {
        role: 'user',
        content: 'How can I make a strong first impression at the Slug Club?',
        time: '9:41 PM',
      },
      {
        role: 'assistant',
        content:
          'A memorable entrance is less about being noticed and more about making others feel seen. Ask a thoughtful question, listen closely, and leave a little room for curiosity. The most elegant influence is never announced.',
        time: '9:41 PM',
      },
      {
        role: 'user',
        content: 'Give me an example of an opening line.',
        time: '9:42 PM',
      },
      {
        role: 'assistant',
        content:
          '“I heard you have a talent for finding the most interesting people in a room — who should I be speaking with?” It is warm, specific, and invites them to share what they know.',
        time: '9:42 PM',
      },
    ],
  },
  {
    id: 'mock-2',
    title: 'A better revision ritual',
    character_id: null,
    persona_id: null,
    messages: [
      {
        role: 'user',
        content: 'Help me build a focused revision routine.',
        time: 'Yesterday',
      },
      {
        role: 'assistant',
        content:
          'Try three quiet rounds: recall what you know without notes, check the gaps, then teach the tricky parts aloud. Keep your desk clear and finish by writing one question to tackle tomorrow.',
        time: 'Yesterday',
      },
    ],
  },
  {
    id: 'mock-3',
    title: 'Potions essay outline',
    character_id: null,
    persona_id: null,
    messages: [
      {
        role: 'user',
        content: 'I need an outline about antidotes and their limits.',
        time: 'Mon',
      },
      {
        role: 'assistant',
        content:
          'Start with the principle that an antidote must be matched to its toxin. Then compare identification, timing, and dosage, before concluding with why prevention and careful labelling matter just as much.',
        time: 'Mon',
      },
    ],
  },
  {
    id: 'mock-4',
    title: 'The greenhouse at dusk',
    character_id: null,
    persona_id: null,
    messages: [
      {
        role: 'user',
        content: 'Write a short atmospheric scene set in a greenhouse.',
        time: 'Sun',
      },
      {
        role: 'assistant',
        content:
          'At dusk, the greenhouse held the last of the day like a secret. Silver leaves stirred though the windows were shut, and somewhere among the pots, a flower opened with a soft, deliberate sigh.',
        time: 'Sun',
      },
    ],
  },
]
