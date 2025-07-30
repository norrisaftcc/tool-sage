# SAGE Testing Guide

This guide helps you manually test SAGE's adaptive learning features.

## Prerequisites

1. **Ollama must be running**:
   ```bash
   ollama serve
   ```

2. **Required models** (pull if needed):
   ```bash
   ollama pull llama2:13b      # For Alpha-level (profile analysis)
   ollama pull deepseek-r1     # For Beta-level (general responses)
   ollama pull llama3.2        # For Gamma/Delta (quick responses)
   ```

3. **Install SAGE** (from project root):
   ```bash
   pip install -e ".[dev]"
   ```

## Quick Test

```bash
# Basic test to verify everything works
sage test
```

## Interactive Learning Session

### Start a basic session:
```bash
sage learn
```

### Start with specific student and topic:
```bash
sage learn -s alice -t "Python functions"
```

## Test Scenarios

### 1. Test Sentiment Detection & Adaptation

Start a session and try these inputs to see adaptation in action:

**Negative sentiment (should trigger support):**
- "I'm really confused about this"
- "This is too hard, I don't understand"
- "I'm frustrated and stuck"

**Expected**: High emotional support, slower pace, simpler explanations

**Positive sentiment (should maintain/accelerate):**
- "This makes sense now, thanks!"
- "Great explanation, I got it"
- "That was easy, what's next?"

**Expected**: Celebratory tone, maintain/increase complexity

### 2. Test Profile Building

On first interaction with a new student ID:
```bash
sage learn -s newstudent
```

The system should:
1. Create a learning profile
2. Ask about learning preferences
3. Adapt based on responses

### 3. Test Session Persistence

```bash
# Start a session
sage learn -s testuser

# Have a conversation, then exit with 'quit'
# Start again with same user
sage learn -s testuser

# Should remember previous interactions
```

### 4. Test Topic-Specific Adaptation

```bash
sage learn -t "recursion"

# Try expressing confusion
"I don't get how recursion works"

# Should adapt explanation style
```

## Debugging Options

### View agent activity:
When prompted `[Debug] Show agent activity?`, answer `y` to see:
- Which agents were activated
- Sentiment analysis results
- Adaptation decisions

### Check persistence:
```bash
# Session data is stored in ~/.sage/data/
ls ~/.sage/data/*/
```

### Monitor Ollama:
```bash
# In another terminal, watch Ollama logs
journalctl -u ollama -f  # If using systemd
# Or check Ollama's console output
```

## Common Issues

1. **"Ollama Error" in responses**
   - Make sure Ollama is running: `ollama serve`
   - Check models are downloaded: `ollama list`

2. **Slow responses**
   - First call to each model takes time to load
   - Larger models (llama2:13b) are slower

3. **Profile parsing errors**
   - The LLM sometimes returns invalid YAML
   - Just continue, it will retry

## Advanced Testing

### Test different fork levels:
The system uses different models for different tasks:
- **Profile analysis**: Uses Alpha (llama2:13b) - slowest, most thoughtful
- **Content adaptation**: Uses Beta (deepseek-r1) - balanced
- **Quick responses**: Uses Gamma/Delta (llama3.2) - fastest

### Test emotional progression:
1. Start neutral
2. Express increasing frustration over 3-4 messages
3. System should detect declining sentiment and increase support
4. Express understanding
5. System should detect improvement and celebrate

## Sample Conversation Flow

```
🎓 SAGE Learning Assistant
Student: alice | Topic: Python basics
--------------------------------------------------

🤖 SAGE: Hello! I'm SAGE, your adaptive learning assistant. Let's start by understanding how you learn best.

📝 You: Hi, I want to learn Python

🤖 SAGE: Great! I'm creating a learning profile for you. What's your preferred learning style - visual, auditory, or hands-on?

📝 You: I'm a visual learner

🤖 SAGE: Perfect! As a visual learner, I'll use diagrams and examples. Let's start with Python basics. What would you like to explore first?

📝 You: Variables, but I'm finding it confusing

🤖 SAGE: I can see this might be challenging. Let's take a step back and approach it differently. Think of variables as labeled boxes where you store values...

📝 You: Oh that makes more sense now!

🤖 SAGE: Fantastic! You're getting it. Ready to try some examples?
```

## Tips for Testing

1. **Vary your language** - Don't just say "confused" repeatedly
2. **Test edge cases** - Empty inputs, very long inputs, mixed signals
3. **Check persistence** - Exit and return to see if state is maintained
4. **Try different topics** - Math, science, programming, etc.
5. **Mix sentiment** - Go from positive to negative and back

Remember: The system is still learning too! Real LLMs make it much more dynamic than mocked responses.