export interface Paper {
  id: string;
  title: string;
  authors: string[];
  year: number;
  cited_by_count: number;
  is_english: boolean;
  abstract: string;
  type: string;
  doi: string;
  concepts: string[];
}

export interface Statistics {
  total: number;
  recent_count: number;
  recent_ratio: number;
  english_count: number;
  english_ratio: number;
  total_citations: number;
  avg_citations: number;
}

export interface ReviewRecord {
  id: number;
  topic: string;
  review: string;
  papers: Paper[];
  statistics: Statistics;
  target_count: number;
  recent_years_ratio: number;
  english_ratio: number;
  status: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface GenerateResponse {
  success: boolean;
  message: string;
  data?: {
    id?: number;
    topic: string;
    review: string;
    papers: Paper[];
    statistics: Statistics;
    created_at?: string;
    // 三圈分析相关
    analysis?: ThreeCirclesAnalysis;
    framework?: ReviewFramework;
    circles?: CircleSummary[];
    gap_analysis?: GapAnalysis;
  };
}

export interface RecordsResponse {
  success: boolean;
  count: number;
  records: ReviewRecord[];
}

// 三圈分析相关类型
export interface ThreeCirclesAnalysis {
  methodology: string;
  domain: string;
  optimization: string;
  title: string;
}

export interface CircleResult {
  circle: string;
  name: string;
  query: string;
  description: string;
  papers: Paper[];
  count: number;
}

export interface CircleSummary {
  circle: string;
  name: string;
  count: number;
}

export interface GapAnalysis {
  gap_description: string;
  research_opportunity: string;
  intersection_count: number;
  suggestions: string[];
}

export interface ReviewFramework {
  introduction: {
    title: string;
    content: string;
  };
  sections: Array<{
    circle: string;
    title: string;
    description: string;
    paper_count: number;
    key_points: string[];
  }>;
  gap_analysis: {
    title: string;
    gap: string;
    opportunity: string;
    suggestions: string[];
  };
}

export interface ThreeCirclesResponse {
  success: boolean;
  message: string;
  data?: {
    analysis: ThreeCirclesAnalysis;
    circles: CircleResult[];
    gap_analysis: GapAnalysis;
    review_framework: ReviewFramework;
  };
}
