import axios from 'axios';

export interface Badge {
  name: string;
  icon: string;
  tier: 'Bronze' | 'Silver' | 'Gold' | 'Diamond' | 'Legendary';
}

export interface Achievement {
  id: number;
  name: string;
  description: string;
  category: string;
  badge: Badge;
  unlocked: boolean;
  unlocked_at?: string;
  xp_reward: number;
  current_value: number;
  target_value: number;
  progress_percentage: number;
}

export interface LevelResponse {
  current_level: number;
  current_xp: number;
  next_level: number;
  xp_to_next_level: number;
  progress_percentage: number;
}

export interface AchievementProgress {
  level: LevelResponse;
  unlocked_count: number;
  total_count: number;
  achievements: Achievement[];
}

const API_BASE = '/api'; // Adjust if proxy needed

export const fetchAchievements = async (): Promise<Achievement[]> => {
  const { data } = await axios.get<Achievement[]>(`${API_BASE}/achievements`);
  return data;
};

export const fetchAchievementProgress = async (): Promise<AchievementProgress> => {
  const { data } = await axios.get<AchievementProgress>(`${API_BASE}/achievements/progress`);
  return data;
};
