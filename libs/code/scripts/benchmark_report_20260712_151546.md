# Volcengine (Huoshan) Model Coding Benchmark Report

- Models tested: 11
- Test cases: 13
- Total evaluations: 143
- Generated: 2026-07-12 17:27:54

## Per-Model Summary

| Model | Avg Score | Avg Elapsed | Avg Output Tokens | Avg Reasoning | Success Rate | Syntax Pass Rate |
|-------|-----------|-------------|-------------------|---------------|--------------|------------------|
| doubao-seed-2.0-code | 53.5 | 175.8s | 8839 | 7883 | 100% | 38% |
| doubao-seed-2.0-pro | 57.5 | 126.2s | 9681 | 8659 | 100% | 38% |
| doubao-seed-2.0-lite | 82.1 | 54.7s | 6413 | 3859 | 100% | 92% |
| doubao-seed-2.0-mini | 68.4 | 63.9s | 9088 | 7193 | 100% | 54% |
| glm-5.2 | 64.1 | 117.6s | 7993 | 0 | 100% | 62% |
| kimi-k2.7-code | 67.5 | 255.1s | 7607 | 5605 | 77% | 69% |
| deepseek-v4-pro | 77.8 | 102.2s | 6378 | 3815 | 100% | 85% |
| deepseek-v4-flash | 74.4 | 35.2s | 3941 | 1328 | 100% | 92% |
| minimax-m3 | 49.3 | 68.4s | 8016 | 0 | 100% | 54% |
| minimax-m2.7 | 71.9 | 147.3s | 8182 | 1675 | 100% | 62% |
| kimi-k2.6 | 67.2 | 219.7s | 8903 | 2100 | 77% | 77% |

## Per-Dimension Breakdown

### Algorithm

| Model | Test | Score | Elapsed | Output Tokens | Syntax | Keywords |
|-------|------|-------|---------|---------------|--------|----------|
| doubao-seed-2.0-code | LRU Cache Implementation | 33.2 | 162.9s | 8192 | FAIL:  | 0% |
| doubao-seed-2.0-code | Dijkstra with Priority Queue | 33.2 | 171.4s | 8192 | FAIL:  | 0% |
| doubao-seed-2.0-code | Token Bucket Rate Limiter (async) | 33.2 | 177.7s | 8192 | FAIL:  | 0% |
| doubao-seed-2.0-pro | LRU Cache Implementation | 52.8 | 104.0s | 8192 | FAIL:  | 67% |
| doubao-seed-2.0-pro | Dijkstra with Priority Queue | 61.9 | 106.8s | 8192 | FAIL:  | 100% |
| doubao-seed-2.0-pro | Token Bucket Rate Limiter (async) | 33.2 | 118.3s | 8192 | FAIL:  | 0% |
| doubao-seed-2.0-lite | Dijkstra with Priority Queue | 83.4 | 42.5s | 5108 | PASS | 100% |
| doubao-seed-2.0-lite | LRU Cache Implementation | 88.5 | 55.6s | 6704 | PASS | 100% |
| doubao-seed-2.0-lite | Token Bucket Rate Limiter (async) | 90.7 | 63.6s | 7628 | PASS | 100% |
| doubao-seed-2.0-mini | Dijkstra with Priority Queue | 84.7 | 54.3s | 7542 | PASS | 80% |
| doubao-seed-2.0-mini | LRU Cache Implementation | 61.7 | 58.0s | 8192 | FAIL:  | 100% |
| doubao-seed-2.0-mini | Token Bucket Rate Limiter (async) | 33.2 | 62.4s | 8192 | FAIL:  | 0% |
| glm-5.2 | Dijkstra with Priority Queue | 82.6 | 86.2s | 6299 | PASS | 100% |
| glm-5.2 | LRU Cache Implementation | 25.0 | 113.1s | 8192 | FAIL:  | 0% |
| glm-5.2 | Token Bucket Rate Limiter (async) | 25.0 | 115.5s | 8192 | FAIL:  | 0% |
| kimi-k2.7-code | Dijkstra with Priority Queue | 87.2 | 164.3s | 6607 | PASS | 100% |
| kimi-k2.7-code | LRU Cache Implementation | 92.9 | 256.3s | 9959 | PASS | 100% |
| kimi-k2.7-code | Token Bucket Rate Limiter (async) | 93.2 | 587.2s | 9474 | PASS | 100% |
| deepseek-v4-pro | LRU Cache Implementation | 79.7 | 61.5s | 3655 | PASS | 100% |
| deepseek-v4-pro | Dijkstra with Priority Queue | 77.3 | 49.0s | 2926 | PASS | 100% |
| deepseek-v4-pro | Token Bucket Rate Limiter (async) | 86.9 | 99.5s | 6065 | PASS | 100% |
| deepseek-v4-flash | LRU Cache Implementation | 76.0 | 23.8s | 2553 | PASS | 100% |
| deepseek-v4-flash | Dijkstra with Priority Queue | 77.9 | 28.6s | 3229 | PASS | 100% |
| deepseek-v4-flash | Token Bucket Rate Limiter (async) | 86.6 | 54.2s | 6331 | PASS | 100% |
| minimax-m3 | LRU Cache Implementation | 25.0 | 71.9s | 8192 | FAIL:  | 0% |
| minimax-m3 | Dijkstra with Priority Queue | 85.0 | 60.4s | 7774 | PASS | 100% |
| minimax-m3 | Token Bucket Rate Limiter (async) | 25.0 | 91.4s | 8192 | FAIL:  | 0% |
| minimax-m2.7 | Dijkstra with Priority Queue | 85.2 | 131.4s | 7147 | PASS | 100% |
| minimax-m2.7 | LRU Cache Implementation | 52.3 | 149.7s | 8192 | FAIL:  | 67% |
| minimax-m2.7 | Token Bucket Rate Limiter (async) | 67.7 | 112.4s | 5508 | FAIL: IndentationError: unexpected indent (line 1) | 100% |
| kimi-k2.6 | Dijkstra with Priority Queue | 91.6 | 215.2s | 8834 | PASS | 100% |
| kimi-k2.6 | LRU Cache Implementation | 93.2 | 262.0s | 11080 | PASS | 100% |
| kimi-k2.6 | Token Bucket Rate Limiter (async) | 0.0 | 0.0s | 0 | FAIL:  | 0% |

### Comprehension

| Model | Test | Score | Elapsed | Output Tokens | Syntax | Keywords |
|-------|------|-------|---------|---------------|--------|----------|
| doubao-seed-2.0-code | Explain Complex Async Decorator | 82.5 | 99.7s | 4803 | PASS | 100% |
| doubao-seed-2.0-pro | Explain Complex Async Decorator | 90.8 | 106.9s | 8192 | PASS | 100% |
| doubao-seed-2.0-lite | Explain Complex Async Decorator | 85.2 | 54.2s | 5613 | PASS | 100% |
| doubao-seed-2.0-mini | Explain Complex Async Decorator | 91.1 | 57.7s | 7774 | PASS | 100% |
| glm-5.2 | Explain Complex Async Decorator | 79.8 | 109.1s | 4883 | PASS | 100% |
| kimi-k2.7-code | Explain Complex Async Decorator | 88.1 | 200.0s | 7099 | PASS | 100% |
| deepseek-v4-pro | Explain Complex Async Decorator | 80.6 | 67.7s | 4013 | PASS | 100% |
| deepseek-v4-flash | Explain Complex Async Decorator | 77.9 | 30.0s | 3367 | PASS | 100% |
| minimax-m3 | Explain Complex Async Decorator | 75.3 | 28.3s | 2664 | PASS | 100% |
| minimax-m2.7 | Explain Complex Async Decorator | 78.5 | 85.1s | 3637 | PASS | 100% |
| kimi-k2.6 | Explain Complex Async Decorator | 86.8 | 215.8s | 6207 | PASS | 100% |

### Debugging

| Model | Test | Score | Elapsed | Output Tokens | Syntax | Keywords |
|-------|------|-------|---------|---------------|--------|----------|
| doubao-seed-2.0-code | Fix Race Condition in Bank Transfer | 33.2 | 173.3s | 8192 | FAIL:  | 0% |
| doubao-seed-2.0-code | Fix Memory Leak in Event Handler | 33.2 | 178.2s | 8192 | FAIL:  | 0% |
| doubao-seed-2.0-pro | Fix Race Condition in Bank Transfer | 33.2 | 115.3s | 8192 | FAIL:  | 0% |
| doubao-seed-2.0-pro | Fix Memory Leak in Event Handler | 33.2 | 113.3s | 8192 | FAIL:  | 0% |
| doubao-seed-2.0-lite | Fix Memory Leak in Event Handler | 62.8 | 36.9s | 3942 | PASS | 40% |
| doubao-seed-2.0-lite | Fix Race Condition in Bank Transfer | 78.9 | 53.7s | 5926 | PASS | 75% |
| doubao-seed-2.0-mini | Fix Race Condition in Bank Transfer | 72.9 | 49.9s | 6447 | PASS | 50% |
| doubao-seed-2.0-mini | Fix Memory Leak in Event Handler | 33.2 | 62.2s | 8192 | FAIL:  | 0% |
| glm-5.2 | Fix Race Condition in Bank Transfer | 76.7 | 70.5s | 3343 | PASS | 100% |
| glm-5.2 | Fix Memory Leak in Event Handler | 74.1 | 70.3s | 5049 | PASS | 80% |
| kimi-k2.7-code | Fix Memory Leak in Event Handler | 83.2 | 204.8s | 6851 | PASS | 80% |
| kimi-k2.7-code | Fix Race Condition in Bank Transfer | 78.8 | 473.6s | 6010 | PASS | 75% |
| deepseek-v4-pro | Fix Race Condition in Bank Transfer | 75.2 | 59.8s | 3538 | PASS | 88% |
| deepseek-v4-pro | Fix Memory Leak in Event Handler | 78.7 | 87.8s | 5236 | PASS | 80% |
| deepseek-v4-flash | Fix Race Condition in Bank Transfer | 70.9 | 24.0s | 2102 | PASS | 88% |
| deepseek-v4-flash | Fix Memory Leak in Event Handler | 73.1 | 33.2s | 3535 | PASS | 80% |
| minimax-m3 | Fix Race Condition in Bank Transfer | 67.5 | 25.3s | 2516 | PASS | 75% |
| minimax-m3 | Fix Memory Leak in Event Handler | 73.4 | 42.8s | 4711 | PASS | 80% |
| minimax-m2.7 | Fix Race Condition in Bank Transfer | 85.7 | 132.5s | 6775 | PASS | 100% |
| minimax-m2.7 | Fix Memory Leak in Event Handler | 65.2 | 65.1s | 3139 | PASS | 60% |
| kimi-k2.6 | Fix Race Condition in Bank Transfer | 85.0 | 427.8s | 11802 | PASS | 100% |
| kimi-k2.6 | Fix Memory Leak in Event Handler | 0.0 | 0.0s | 0 | FAIL:  | 0% |

### Project Generation

| Model | Test | Score | Elapsed | Output Tokens | Syntax | Keywords |
|-------|------|-------|---------|---------------|--------|----------|
| doubao-seed-2.0-code | Complete REST API Project with SQLite | 81.2 | 94.1s | 5558 | PASS | 100% |
| doubao-seed-2.0-code | CLI Tool with Subcommands (Click) | 67.3 | 219.7s | 12288 | PASS | 0% |
| doubao-seed-2.0-pro | Complete REST API Project with SQLite | 82.2 | 153.9s | 12288 | PASS | 55% |
| doubao-seed-2.0-pro | CLI Tool with Subcommands (Click) | 67.3 | 151.9s | 12288 | PASS | 0% |
| doubao-seed-2.0-lite | Complete REST API Project with SQLite | 85.2 | 53.5s | 6440 | PASS | 100% |
| doubao-seed-2.0-lite | CLI Tool with Subcommands (Click) | 86.8 | 71.1s | 8874 | PASS | 100% |
| doubao-seed-2.0-mini | Complete REST API Project with SQLite | 91.5 | 72.7s | 10842 | PASS | 100% |
| doubao-seed-2.0-mini | CLI Tool with Subcommands (Click) | 78.6 | 84.4s | 12288 | PASS | 45% |
| glm-5.2 | Complete REST API Project with SQLite | 82.3 | 133.9s | 12288 | PASS | 91% |
| glm-5.2 | CLI Tool with Subcommands (Click) | 85.0 | 207.4s | 12288 | PASS | 100% |
| kimi-k2.7-code | Complete REST API Project with SQLite | 90.8 | 818.7s | 10187 | PASS | 100% |
| kimi-k2.7-code | CLI Tool with Subcommands (Click) | 0.0 | 0.0s | 0 | FAIL:  | 0% |
| deepseek-v4-pro | Complete REST API Project with SQLite | 90.0 | 138.5s | 9259 | PASS | 100% |
| deepseek-v4-pro | CLI Tool with Subcommands (Click) | 87.4 | 162.1s | 10500 | PASS | 100% |
| deepseek-v4-flash | CLI Tool with Subcommands (Click) | 45.1 | 8.9s | 929 | PASS | 9% |
| deepseek-v4-flash | Complete REST API Project with SQLite | 80.1 | 41.0s | 4883 | PASS | 100% |
| minimax-m3 | Complete REST API Project with SQLite | 55.0 | 92.3s | 12288 | PASS | 0% |
| minimax-m3 | CLI Tool with Subcommands (Click) | 55.0 | 89.0s | 12288 | PASS | 0% |
| minimax-m2.7 | Complete REST API Project with SQLite | 85.2 | 190.2s | 12288 | PASS | 100% |
| minimax-m2.7 | CLI Tool with Subcommands (Click) | 74.8 | 196.5s | 12288 | PASS | 64% |
| kimi-k2.6 | Complete REST API Project with SQLite | 84.9 | 70.4s | 7458 | PASS | 100% |
| kimi-k2.6 | CLI Tool with Subcommands (Click) | 85.0 | 487.9s | 16783 | PASS | 100% |

### Refactoring

| Model | Test | Score | Elapsed | Output Tokens | Syntax | Keywords |
|-------|------|-------|---------|---------------|--------|----------|
| doubao-seed-2.0-code | Refactor God Class into SRP Modules | 92.4 | 197.8s | 10341 | PASS | 100% |
| doubao-seed-2.0-pro | Refactor God Class into SRP Modules | 91.2 | 144.5s | 12288 | PASS | 86% |
| doubao-seed-2.0-lite | Refactor God Class into SRP Modules | 85.7 | 48.9s | 5969 | PASS | 100% |
| doubao-seed-2.0-mini | Refactor God Class into SRP Modules | 89.9 | 54.3s | 7712 | PASS | 100% |
| glm-5.2 | Refactor God Class into SRP Modules | 83.4 | 80.9s | 6702 | PASS | 100% |
| kimi-k2.7-code | Refactor God Class into SRP Modules | 93.0 | 178.0s | 10887 | PASS | 100% |
| deepseek-v4-pro | Refactor God Class into SRP Modules | 83.6 | 81.3s | 5245 | PASS | 100% |
| deepseek-v4-flash | Refactor God Class into SRP Modules | 78.2 | 29.9s | 3715 | PASS | 100% |
| minimax-m3 | Refactor God Class into SRP Modules | 79.2 | 31.0s | 4622 | PASS | 100% |
| minimax-m2.7 | Refactor God Class into SRP Modules | 84.9 | 129.0s | 6426 | PASS | 100% |
| kimi-k2.6 | Refactor God Class into SRP Modules | 92.1 | 234.6s | 9816 | PASS | 100% |

### Robustness

| Model | Test | Score | Elapsed | Output Tokens | Syntax | Keywords |
|-------|------|-------|---------|---------------|--------|----------|
| doubao-seed-2.0-code | HTTP Client with Circuit Breaker | 61.3 | 143.6s | 8192 | FAIL:  | 100% |
| doubao-seed-2.0-code | Robust CSV Parser with Edge Cases | 33.2 | 163.0s | 8192 | FAIL:  | 0% |
| doubao-seed-2.0-pro | Robust CSV Parser with Edge Cases | 33.2 | 110.2s | 8192 | FAIL:  | 0% |
| doubao-seed-2.0-pro | HTTP Client with Circuit Breaker | 33.2 | 105.8s | 8192 | FAIL:  | 0% |
| doubao-seed-2.0-lite | Robust CSV Parser with Edge Cases | 87.7 | 61.6s | 6728 | PASS | 100% |
| doubao-seed-2.0-lite | HTTP Client with Circuit Breaker | 61.0 | 65.7s | 8192 | FAIL:  | 100% |
| doubao-seed-2.0-mini | Robust CSV Parser with Edge Cases | 33.2 | 56.8s | 8192 | FAIL:  | 0% |
| doubao-seed-2.0-mini | HTTP Client with Circuit Breaker | 60.9 | 60.4s | 8192 | FAIL:  | 100% |
| glm-5.2 | Robust CSV Parser with Edge Cases | 55.0 | 166.4s | 8192 | FAIL:  | 100% |
| glm-5.2 | HTTP Client with Circuit Breaker | 25.0 | 130.8s | 8192 | FAIL:  | 0% |
| kimi-k2.7-code | Robust CSV Parser with Edge Cases | 73.8 | 222.1s | 17415 | FAIL: SyntaxError: unterminated string literal (detected at line 418) (line 418) | 100% |
| kimi-k2.7-code | HTTP Client with Circuit Breaker | 0.0 | 0.0s | 0 | FAIL:  | 0% |
| deepseek-v4-pro | Robust CSV Parser with Edge Cases | 33.2 | 138.7s | 8193 | FAIL:  | 0% |
| deepseek-v4-pro | HTTP Client with Circuit Breaker | 59.3 | 129.2s | 8193 | FAIL:  | 100% |
| deepseek-v4-flash | HTTP Client with Circuit Breaker | 78.4 | 32.8s | 3875 | PASS | 100% |
| deepseek-v4-flash | Robust CSV Parser with Edge Cases | 56.7 | 45.1s | 4868 | FAIL: SyntaxError: unterminated string literal (detected at line 326) (line 326) | 100% |
| minimax-m3 | Robust CSV Parser with Edge Cases | 25.0 | 93.1s | 8192 | FAIL:  | 0% |
| minimax-m3 | HTTP Client with Circuit Breaker | 25.0 | 61.1s | 8192 | FAIL:  | 0% |
| minimax-m2.7 | Robust CSV Parser with Edge Cases | 57.2 | 163.2s | 8192 | FAIL:  | 100% |
| minimax-m2.7 | HTTP Client with Circuit Breaker | 55.2 | 126.5s | 8192 | FAIL:  | 100% |
| kimi-k2.6 | HTTP Client with Circuit Breaker | 84.9 | 539.2s | 6974 | PASS | 100% |
| kimi-k2.6 | Robust CSV Parser with Edge Cases | 0.0 | 0.0s | 0 | FAIL:  | 0% |

### System Design

| Model | Test | Score | Elapsed | Output Tokens | Syntax | Keywords |
|-------|------|-------|---------|---------------|--------|----------|
| doubao-seed-2.0-code | Event-Driven Architecture Design | 37.3 | 255.6s | 12288 | FAIL:  | 0% |
| doubao-seed-2.0-code | Plugin Architecture with Hot Reload | 74.6 | 248.1s | 12288 | PASS | 25% |
| doubao-seed-2.0-pro | Plugin Architecture with Hot Reload | 90.4 | 141.2s | 11160 | PASS | 100% |
| doubao-seed-2.0-pro | Event-Driven Architecture Design | 44.5 | 168.4s | 12288 | FAIL:  | 25% |
| doubao-seed-2.0-lite | Event-Driven Architecture Design | 85.8 | 48.8s | 5955 | PASS | 100% |
| doubao-seed-2.0-lite | Plugin Architecture with Hot Reload | 85.4 | 54.8s | 6285 | PASS | 100% |
| doubao-seed-2.0-mini | Plugin Architecture with Hot Reload | 93.4 | 77.4s | 12288 | PASS | 100% |
| doubao-seed-2.0-mini | Event-Driven Architecture Design | 64.7 | 81.0s | 12288 | FAIL:  | 100% |
| glm-5.2 | Event-Driven Architecture Design | 85.0 | 98.8s | 8001 | PASS | 100% |
| glm-5.2 | Plugin Architecture with Hot Reload | 55.0 | 145.5s | 12288 | FAIL:  | 100% |
| kimi-k2.7-code | Event-Driven Architecture Design | 96.5 | 210.6s | 14402 | PASS | 100% |
| kimi-k2.7-code | Plugin Architecture with Hot Reload | 0.0 | 0.0s | 0 | FAIL:  | 0% |
| deepseek-v4-pro | Event-Driven Architecture Design | 88.9 | 118.6s | 7214 | PASS | 100% |
| deepseek-v4-pro | Plugin Architecture with Hot Reload | 90.0 | 135.6s | 8874 | PASS | 100% |
| deepseek-v4-flash | Event-Driven Architecture Design | 81.0 | 42.8s | 4588 | PASS | 100% |
| deepseek-v4-flash | Plugin Architecture with Hot Reload | 85.6 | 63.7s | 7259 | PASS | 100% |
| minimax-m3 | Event-Driven Architecture Design | 25.0 | 102.0s | 12288 | FAIL:  | 0% |
| minimax-m3 | Plugin Architecture with Hot Reload | 25.0 | 101.1s | 12288 | FAIL:  | 0% |
| minimax-m2.7 | Event-Driven Architecture Design | 55.5 | 208.8s | 12288 | FAIL:  | 100% |
| minimax-m2.7 | Plugin Architecture with Hot Reload | 86.9 | 225.0s | 12288 | PASS | 100% |
| kimi-k2.6 | Event-Driven Architecture Design | 85.0 | 184.2s | 16228 | PASS | 100% |
| kimi-k2.6 | Plugin Architecture with Hot Reload | 85.0 | 219.2s | 20551 | PASS | 100% |

## Errors

### kimi-k2.7-code - Plugin Architecture with Hot Reload
```
APITimeoutError: Request timed out.
```

### kimi-k2.7-code - CLI Tool with Subcommands (Click)
```
APITimeoutError: Request timed out.
```

### kimi-k2.7-code - HTTP Client with Circuit Breaker
```
APITimeoutError: Request timed out.
```

### kimi-k2.6 - Token Bucket Rate Limiter (async)
```
APITimeoutError: Request timed out.
```

### kimi-k2.6 - Fix Memory Leak in Event Handler
```
APITimeoutError: Request timed out.
```

### kimi-k2.6 - Robust CSV Parser with Edge Cases
```
APITimeoutError: Request timed out.
```
