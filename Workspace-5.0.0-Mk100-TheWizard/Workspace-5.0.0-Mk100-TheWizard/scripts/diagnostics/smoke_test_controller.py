import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path("/app/src")))
sys.path.append(str(Path("src").resolve()))

try:
    from jarvis.arches.controller import get_controller, PlanStage
    
    print("✅ Import successful")
    
    controller = get_controller()
    print("✅ Instantiated controller")
    
    session = controller.start_session("Test Query")
    print(f"✅ Started session: {session.session_id}")
    
    controller.start_stage(session, PlanStage.HYBRID)
    print("✅ Started stage")
    
    controller.complete_stage(session, PlanStage.HYBRID)
    print("✅ Completed stage")
    
    print("🎉 ARCHES Controller is working!")

except Exception as e:
    print(f"❌ Failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
