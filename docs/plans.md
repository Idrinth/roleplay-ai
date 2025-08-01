# Roleplay AI Architecture Summary

**Goal**: Build a roleplay AI that overcomes contexct window limitations and provides reliable long-form storytelling.

## Database Layer
- **Qdrant**: Vector database for semantic story search (10 results per query)
- **MongoDB**: Character sheets with flexible schema for easy updates
- **MariaDB**: Conversation history in structured SQL
- **Redis**: Cache for summaries (world state, party state, story history)

## Context Assembly
- Location-aware vector search results
- Recent conversation messages  
- Character sheets for active characters
- Cached summaries of world/party state and story history

## LLM Strategy
- **Primary**: Self-hosted Llama (cost control, portability)

## Processing Flow

### Fast Path (immediate user response):
1. Retrieve context from all databases
2. Add query to databases
3. Get LLM response
4. Return to user immediately

### Background Path (async after response):
5. Add response to databases
6. Update character sheets via small LLM call
7. Update summaries via small LLM call
8. Refresh Redis cache

## User Experience
- Block message sending during background processing
- Disabled send button with informative tooltips
- Sub-second perceived response time
- Prevents consistency issues from overlapping requests
