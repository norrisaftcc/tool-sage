"""CLI interface for SAGE learning assistant."""

import click
import json
from datetime import datetime
from pathlib import Path
from sage.core.base import Flow, SharedStore
from sage.core.persistence import ProfilePersistence, JSONPersistence
from sage.agents.orchestrator import AssistanceOrchestratorNode
from sage.agents.profile import LearningProfileNode
from sage.agents.responder import ResponseGeneratorNode
from sage.agents.adapter import ContentAdaptationNode


def save_session(flow: Flow, profile_persistence: ProfilePersistence, student_id: str) -> None:
    """Save the current session data."""
    profiles = flow.shared.get("student_profiles", {})
    
    if student_id in profiles:
        profile = profiles[student_id]
        
        # Update interaction history
        profile["interaction_history"] = flow.shared.get("interactions", [])
        profile["last_topic"] = flow.shared.get("topic", "general")
        profile["total_sessions"] = profile.get("total_sessions", 0) + 1
        
        # Save the updated profile
        profile_persistence.save_profile(student_id, profile)
        
        # Also save session summary at delta level
        summary = f"Worked on {profile['last_topic']}, {len(flow.shared.get('conversation', []))} exchanges"
        profile_persistence.save_summary(student_id, summary)


def export_conversation(flow: Flow, student_id: str, topic: str) -> Path:
    """Export the current conversation to a file."""
    # Create conversations directory
    conv_dir = Path.home() / ".sage" / "conversations"
    conv_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sage_conversation_{student_id}_{timestamp}.json"
    filepath = conv_dir / filename
    
    # Gather conversation data
    conversation_data = {
        "student_id": student_id,
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "conversation": flow.shared.get("conversation", []),
        "adaptations": [],
        "agent_logs": flow.shared.get("logs", []),
        "flow_history": flow.history,
        "profile": flow.shared.get("student_profiles", {}).get(student_id, {}),
        "total_exchanges": len(flow.shared.get("conversation", [])),
    }
    
    # Extract adaptation history from logs
    for log in flow.shared.get("logs", []):
        if log.get("agent") == "ContentAdapter":
            conversation_data["adaptations"].append({
                "sentiment": log.get("sentiment"),
                "adaptations": log.get("adaptations", {})
            })
    
    # Write to file
    with open(filepath, 'w') as f:
        json.dump(conversation_data, f, indent=2, sort_keys=True)
    
    return filepath


def create_sage_flow() -> Flow:
    """Create and wire up the SAGE agent flow."""
    # Initialize agents
    orchestrator = AssistanceOrchestratorNode(name="orchestrator")
    profile_agent = LearningProfileNode(name="profile")
    responder = ResponseGeneratorNode(name="respond")
    adapter = ContentAdaptationNode(name="adapt")
    
    # Wire up the flow
    # Orchestrator decides which agent to activate
    orchestrator >> {
        "profile": profile_agent,
        "respond": responder,
        "adapt": adapter,  # Content adaptation based on sentiment
        "question": responder,  # Placeholder
        "progress": responder,  # Placeholder
        "end": None  # Termination state
    }
    
    # Profile agent returns to orchestrator for next decision
    profile_agent >> orchestrator
    
    # Adapter analyzes and goes to responder
    adapter >> responder
    
    # Responder ends the flow cycle (no return to orchestrator)
    # This prevents infinite loops
    
    # Create flow with persistent shared state
    persistence = JSONPersistence()
    shared = SharedStore(persistence=persistence)
    
    flow = Flow(shared=shared)
    
    # Initialize shared store
    flow.shared.update({
        "student_profiles": {},
        "interactions": [],
        "conversation": [],
        "current_student": "default_student",
        "learning_state": "initial"
    })
    
    flow.set_start(orchestrator)
    
    return flow


@click.group()
def cli():
    """SAGE - Scholar's Adaptive Growth Engine"""
    pass


@cli.command()
@click.option('--student', '-s', default='default_student', help='Student ID')
@click.option('--topic', '-t', default='general', help='Learning topic')
@click.option('--export/--no-export', default=True, help='Export conversation on exit')
def learn(student: str, topic: str, export: bool):
    """Start an interactive learning session."""
    click.echo(click.style("🎓 SAGE Learning Assistant", fg='cyan', bold=True))
    click.echo(f"Student: {student} | Topic: {topic}")
    click.echo("-" * 50)
    
    # Create the flow
    flow = create_sage_flow()
    flow.shared["current_student"] = student
    flow.shared["topic"] = topic
    
    # Load existing profile if available
    profile_persistence = ProfilePersistence(flow.shared.persistence)
    existing_profile = profile_persistence.load_profile(student)
    
    if existing_profile:
        click.echo(f"✨ Welcome back! Loading your profile...")
        flow.shared["student_profiles"][student] = existing_profile
        # Load conversation history too
        flow.shared["interactions"] = existing_profile.get("interaction_history", [])
    
    # Initial run to get first response
    flow.run(max_steps=10)
    
    # Display initial response
    response = flow.shared.get("current_response", "Hello! I'm SAGE, your learning assistant.")
    click.echo(f"\n🤖 SAGE: {response}")
    
    # Interactive loop
    conversation_ended = False
    
    while True:
        try:
            # Get student input
            user_input = click.prompt('\n📝 You', type=str)
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                conversation_ended = True
                break
            
            # Special commands
            if user_input.lower() == '/export':
                filepath = export_conversation(flow, student, topic)
                click.echo(f"💾 Conversation exported to: {filepath}")
                continue
            elif user_input.lower() == '/help':
                click.echo("\nCommands:")
                click.echo("  /export - Export current conversation")
                click.echo("  /help   - Show this help")
                click.echo("  exit    - End session and save")
                continue
            
            # Process input
            flow.shared["student_input"] = user_input
            
            # Add to conversation history
            flow.shared["conversation"].append({
                "role": "student",
                "content": user_input
            })
            
            # Run the flow
            flow.run(max_steps=10)
            
            # Display response
            response = flow.shared.get("current_response", "I'm processing that...")
            click.echo(f"\n🤖 SAGE: {response}")
            
            # Debug info (remove in production)
            if click.confirm('\n[Debug] Show agent activity?', default=False):
                logs = flow.shared.get("logs", [])
                for log in logs[-3:]:  # Show last 3 log entries
                    click.echo(f"  - {log}")
                    
        except KeyboardInterrupt:
            conversation_ended = True
            break
        except Exception as e:
            click.echo(f"\n❌ Error: {e}")
            if click.confirm('Continue?', default=True):
                continue
            else:
                conversation_ended = True
                break
    
    # Save session and optionally export
    save_session(flow, profile_persistence, student)
    
    if conversation_ended and export:
        try:
            filepath = export_conversation(flow, student, topic)
            click.echo(f"\n💾 Conversation saved to: {filepath}")
            click.echo(f"   Review with: cat {filepath} | jq .")
        except Exception as e:
            click.echo(f"\n⚠️  Could not export conversation: {e}")
    
    click.echo("\n👋 Thanks for learning with SAGE! See you next time.")


@cli.command()
def test():
    """Run a test conversation to verify the system works."""
    click.echo("🧪 Testing SAGE system...")
    
    # Create flow
    flow = create_sage_flow()
    
    # Simulate a conversation
    test_inputs = [
        "Hello",
        "I want to learn about Python",
        "Can you test me?"
    ]
    
    for input_text in test_inputs:
        click.echo(f"\n📝 Student: {input_text}")
        flow.shared["student_input"] = input_text
        flow.run(max_steps=5)
        response = flow.shared.get("current_response", "No response")
        click.echo(f"🤖 SAGE: {response}")
    
    click.echo("\n✅ Test complete!")
    
    # Show flow history
    click.echo(f"\nFlow history: {' -> '.join(flow.history)}")


@cli.command()
@click.option('--student', '-s', help='Filter by student ID')
@click.option('--limit', '-n', default=10, help='Number of conversations to list')
def history(student: str, limit: int):
    """List saved conversations."""
    conv_dir = Path.home() / ".sage" / "conversations"
    
    if not conv_dir.exists():
        click.echo("No conversations found.")
        return
    
    # Get all conversation files
    files = sorted(conv_dir.glob("sage_conversation_*.json"), reverse=True)
    
    # Filter by student if specified
    if student:
        files = [f for f in files if f"_{student}_" in f.name]
    
    # Limit results
    files = files[:limit]
    
    if not files:
        click.echo("No conversations found matching criteria.")
        return
    
    click.echo(click.style("📚 Saved Conversations", fg='cyan', bold=True))
    click.echo("-" * 60)
    
    for filepath in files:
        try:
            with open(filepath) as f:
                data = json.load(f)
            
            timestamp = datetime.fromisoformat(data['timestamp'])
            student_id = data['student_id']
            topic = data['topic']
            exchanges = data['total_exchanges']
            
            click.echo(f"\n📄 {filepath.name}")
            click.echo(f"   Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"   Student: {student_id} | Topic: {topic}")
            click.echo(f"   Exchanges: {exchanges}")
            
            # Show sentiment summary if available
            adaptations = data.get('adaptations', [])
            if adaptations:
                sentiments = [a['sentiment'] for a in adaptations if a.get('sentiment')]
                if sentiments:
                    click.echo(f"   Sentiments: {' → '.join(sentiments[:5])}")
                    
        except Exception as e:
            click.echo(f"   ⚠️  Error reading file: {e}")
    
    click.echo(f"\n💡 View a conversation with: cat {conv_dir}/[filename] | jq .")


if __name__ == '__main__':
    cli()