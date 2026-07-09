import re

# Read file
with open('src/jarvis/controllers/chat_controller.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define pattern to match (32 lines from 121-152)
old_block = '''        research_summary = None
        if research_trigger:
            # Check rate limit before proceeding
            research_limiter = ResearchLimiter(self.research_limit_config)
            allowed, count = research_limiter.check_limit(request.user_id)
            if not allowed:
                logger.warning("research_rate_limited", user_id=request.user_id, current_count=count)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Hourly research limit reached ({count}/{self.research_limit_config.hourly_limit})"
                )

            arches_controller.set_flag(arches_session, "is_research_triggered", True)
            arches_controller.start_stage(arches_session, PlanStage.RESEARCH)
            
            # Execute Research
            plan = self.planner.plan(request.message, gap_analysis)
            research_results = self.executor.execute(plan)
            integration = self.integrator.integrate(request.message, results, research_results)
            
            research_summary = ChatResearchSummary(
                triggered=True,
                reason=getattr(plan, 'reasoning', "gap_detected"),
                planned_queries=[q.query for q in plan.queries],
                executed_queries=len(research_results),
                sources_collected=sum(len(r.sources) for r in research_results),
                confidence_before=integration.confidence_before,
                confidence_after=integration.confidence_after,
                confidence_delta=integration.delta
            )
            
            arches_controller.complete_stage(arches_session, PlanStage.RESEARCH)'''

# New simplified block (7 lines)
new_block = '''        research_summary = None
        if research_trigger:
            research_summary = self._execute_research(
                request, arches_controller, arches_session, gap_analysis, results
            )
            arches_controller.complete_stage(arches_session, PlanStage.RESEARCH)'''

# Replace
new_content = content.replace(old_block, new_block)

# Write back
with open('src/jarvis/controllers/chat_controller.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Replaced inline research block with helper method call")
print(f"Reduced from {len(old_block.splitlines())} lines to {len(new_block.splitlines())} lines (delta: -{len(old_block.splitlines()) - len(new_block.splitlines())} lines)")
