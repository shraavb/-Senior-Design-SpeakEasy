# Model Selector Implementation

```typescript
import { ModelConfig, ConversationContext } from './config.ts';

export class ModelSelector {
  private configs: ModelConfig[];
  
  constructor(configs: ModelConfig[]) {
    this.configs = configs;
  }
  
  selectModel(context: ConversationContext): ModelConfig {
    const { userPreference, scenario, language, level } = context;
    
    // A/B testing logic
    if (this.isInABTest(userPreference.userId)) {
      return this.getABTestModel(userPreference.userId);
    }
    
    // Context-based selection
    if (scenario === 'casual' || userPreference.style === 'informal') {
      return this.getBestModel('tuned');
    }
    
    // Performance-based selection
    return this.getBestPerformingModel();
  }
  
  private isInABTest(userId: string): boolean {
    // Simple hash-based A/B testing
    const hash = this.hashUserId(userId);
    return hash % 100 < 50; // 50% of users get new model
  }
  
  private getABTestModel(userId: string): ModelConfig {
    const hash = this.hashUserId(userId);
    return hash % 2 === 0 
      ? this.configs.find(c => c.id === 'base-model')!
      : this.configs.find(c => c.id === 'colloquial-model')!;
  }
  
  private getBestModel(type: 'base' | 'tuned' | 'personalized'): ModelConfig {
    return this.configs
      .filter(c => c.type === type)
      .sort((a, b) => b.metadata.performance.naturalnessScore - a.metadata.performance.naturalnessScore)[0];
  }
  
  private getBestPerformingModel(): ModelConfig {
    return this.configs
      .sort((a, b) => {
        const scoreA = this.calculateOverallScore(a);
        const scoreB = this.calculateOverallScore(b);
        return scoreB - scoreA;
      })[0];
  }
  
  private calculateOverallScore(config: ModelConfig): number {
    const { naturalnessScore, engagementScore, accuracyScore } = config.metadata.performance;
    return (naturalnessScore * 0.4) + (engagementScore * 0.4) + (accuracyScore * 0.2);
  }
  
  private hashUserId(userId: string): number {
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      const char = userId.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }
}
```
