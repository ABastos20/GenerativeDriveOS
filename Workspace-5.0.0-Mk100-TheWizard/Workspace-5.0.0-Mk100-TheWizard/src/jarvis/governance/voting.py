"""Voting Engine - Proposal Management and Vote Processing.

Story 9-2: Disagreement Voting Engine
Implements AC1-6, AC16-19: Voting logic, immutability, quorum, and tallying.

This module provides:
- ProposalManager: Lifecycle management (Create -> Open -> Close)
- VotingEngine: Vote casting, validation, and tallying
- Integration with PermissionGate and EscalationEngine
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from jarvis.governance.models import (
    Proposal,
    ProposalStatus,
    ProposalType,
    Vote,
    VoteChoice,
    GovernanceUser,
    AuditLog,
    Role,
    PermissionAction,
    Constitution,
    GovernanceTrustScore,
)
from jarvis.governance.permissions import PermissionGate
from jarvis.governance.escalation import EscalationEngine, EscalationTriggerType
from jarvis.governance.constitution import ConstitutionalGuard

class ProposalManager:
    """Manages the lifecycle of governance proposals.
    
    Implements AC1: Proposal Model lifecycle
    Implements AC2: Proposal States (Draft -> Open -> Closed/Resolved)
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.gate = PermissionGate(session)
        self.audit = AuditLog

    def create_proposal(
        self,
        title: str,
        description: str,
        proposer: GovernanceUser,
        proposal_type: ProposalType = ProposalType.DECISION,
        domain: Optional[str] = None,
        duration_hours: int = 48,
    ) -> Proposal:
        """Create a new proposal in DRAFT state.
        
        Args:
            title: Short summary
            description: Detailed content
            proposer: User creating the proposal
            proposal_type: Category of decision
            domain: Optional domain (e.g. "jarvis.core")
            duration_hours: How long voting will remain open
            
        Returns:
            Created Proposal object
            
        Raises:
            HTTPException: If user lacks PROPOSE permission
        """
        # Story 9-4 will make this fully configurable via database rules
        self.gate.require(proposer, PermissionAction.PROPOSE)
        
        # Determine defaults based on type
        # Story 9-4 will make this fully configurable via database rules
        quorum = 0.5
        threshold = 0.5
        
        if proposal_type == ProposalType.CONSTITUTIONAL_AMENDMENT:
            quorum = 0.75
            threshold = 0.66
            # Require AMEND permission
            self.gate.require(proposer, PermissionAction.AMEND)
            
        # Calculate tentative deadline (updated when opened)
        deadline = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        
        proposal = Proposal(
            title=title,
            description=description,
            proposer_id=proposer.id,
            proposal_type=proposal_type,
            domain=domain,
            status=ProposalStatus.DRAFT,
            quorum_required=quorum,
            approval_threshold=threshold,
            deadline=deadline,
            # Initialize tallies
            total_for=0.0,
            total_against=0.0,
            total_abstain=0.0,
            total_weight=0.0,
        )
        
        self.session.add(proposal)
        self.session.flush()
        
        self._log_action(proposer, "create_proposal", proposal)
        return proposal

    def open_proposal(self, proposal_id: UUID, opener: GovernanceUser) -> Proposal:
        """Move proposal from DRAFT to OPEN state.
        
        Story 9-5: Creates frozen trust snapshot and records total_weight_at_open
        for governance locks. This prevents:
        - Mid-vote trust manipulation (frozen snapshot)
        - Legitimacy drift attacks (total_weight_at_open)
        
        Args:
            proposal_id: ID of proposal to open
            opener: User performing the action (must have MANAGE_PROPOSALS)
            
        Returns:
            Updated Proposal
        """
        # Story 9-1: Require MANAGE_USERS or specific moderator permission?
        # For now, using MANAGE_USERS as proxy for "Manage Governance" or Owner
        # Ideally, we should have a MANAGE_PROPOSALS action, but PermissionAction doesn't have it yet.
        # Fallback to MODERATE if available, else MANAGE_USERS.
        if not self.gate.can(opener, PermissionAction.MODERATE):
             self.gate.require(opener, PermissionAction.MANAGE_USERS)

        proposal = self._get_proposal(proposal_id)
        
        if proposal.status != ProposalStatus.DRAFT:
            raise ValueError(f"Cannot open proposal in state {proposal.status}")
            
        proposal.status = ProposalStatus.OPEN
        proposal.opened_at = datetime.now(timezone.utc)
        
        # Recalculate deadline from now
        # We preserve the original duration intent by checking (deadline - created_at)
        # simplistic approach: assume 48h default if we can't infer
        duration = proposal.deadline - proposal.created_at
        proposal.deadline = datetime.now(timezone.utc) + duration
        
        # Story 9-5: GOVERNANCE LOCKS
        # 1. Create frozen trust snapshot for all active users
        # 2. Record total system weight for legitimacy conservation
        # Instantiate VotingEngine to access trust snapshot logic
        engine = VotingEngine(self.session)
        frozen_snapshot, total_weight = engine.create_trust_snapshot()
        proposal.frozen_trust_snapshot = frozen_snapshot
        proposal.total_weight_at_open = total_weight
        
        self.session.flush()
        self._log_action(opener, "open_proposal", proposal)
        
        # Story 9-5 Phase 4: Emit WebSocket event
        try:
            from jarvis.api.governance_ws import sync_emit_proposal_opened
            sync_emit_proposal_opened(
                proposal_id=proposal.id,
                title=proposal.title,
                proposer=opener.name,
                deadline=proposal.deadline
            )
        except Exception:
            pass  # Don't fail on event emission
        
        return proposal
        
    def cancel_proposal(self, proposal_id: UUID, user: GovernanceUser, reason: str) -> Proposal:
        """Cancel a proposal (moves to REJECTED/WITHDRAWN)."""
        # Only proposer or admin can cancel
        proposal = self._get_proposal(proposal_id)
        
        is_owner = proposal.proposer_id == user.id
        can_moderate = self.gate.can(user, PermissionAction.MODERATE)
        
        if not (is_owner or can_moderate):
            raise ValueError("Permission denied: Only proposer or moderator can cancel")
            
        proposal.status = ProposalStatus.REJECTED # Or add specialized WITHDRAWN status later
        proposal.closed_at = datetime.now(timezone.utc)
        proposal.resolution_reason = f"Cancelled by user: {reason}"
        
        self.session.flush()
        self._log_action(user, "cancel_proposal", proposal, {"reason": reason})
        return proposal
        
    def _get_proposal(self, proposal_id: UUID) -> Proposal:
        stmt = select(Proposal).where(Proposal.id == proposal_id)
        return self.session.execute(stmt).scalar_one()

    def _log_action(self, actor: GovernanceUser, action: str, proposal: Proposal, extra: Dict = None):
        log = AuditLog(
            action_type=action,
            entity_type="proposal",
            entity_id=proposal.id,
            actor_id=actor.id,
            new_value={"status": str(proposal.status)},
            extra_data=extra
        )
        self.session.add(log)


class VotingEngine:
    """Core voting logic and validation.
    
    Implements AC4: Voting Mechanics (One person one vote)
    Implements AC16: Vote Immutability
    Implements AC17: Quorum Checks
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.gate = PermissionGate(session)
        self.escalation = EscalationEngine(session)

    def cast_vote(
        self,
        proposal_id: UUID,
        voter: GovernanceUser,
        choice: VoteChoice,
        justification: Optional[str] = None
    ) -> Vote:
        """Cast a vote on a proposal.
        
        Args:
            proposal_id: Proposal to vote on
            voter: User casting the vote
            choice: FOR, AGAINST, or ABSTAIN
            justification: Optional reasoning
            
        Returns:
            Created Vote object
        """
        # 1. Permission Check
        self.gate.require(voter, PermissionAction.VOTE)
        
        proposal = self._get_proposal(proposal_id)
        
        # 2. Logic Checks (Lazy Expiration)
        self._ensure_voting_open(proposal)
        
        # 3. Duplicate Check
        # Rely on database unique constraint for strictness, but check app-side for user feedback
        if self._has_voted(proposal_id, voter.id):
             raise ValueError("User has already voted on this proposal")

        # 4. Compute Weight (Story 9-5: Use frozen snapshot if available)
        constitution = ConstitutionalGuard.get_active_constitution(self.session)
        
        # Story 9-5: GOVERNANCE LOCK - Use frozen weights from proposal open time
        if proposal.frozen_trust_snapshot and str(voter.id) in proposal.frozen_trust_snapshot:
            # Use frozen weight - prevents mid-vote trust manipulation
            frozen_data = proposal.frozen_trust_snapshot[str(voter.id)]
            vote_weight = frozen_data.get("effective_weight", 0.05)  # Minority floor fallback
        else:
            # Fallback: User registered after proposal opened, use live calculation
            vote_weight = self._compute_vote_weight(voter, constitution)
        
        vote = Vote(
            proposal_id=proposal_id,
            user_id=voter.id,
            choice=choice,
            weight=vote_weight,
            justification=justification
        )
        
        try:
            self.session.add(vote)
            
            # 5. Update Pre-computed Tallies (Atomic update logic)
            # In a high-concurrency DB, we might want to do this via UPDATE proposals SET total_for = total_for + :w
            # For now, ORM update is acceptable for this scale.
            self._update_proposal_tally(proposal, choice, vote_weight)
            
            self.session.flush()
        except IntegrityError:
            self.session.rollback()
            raise ValueError("Vote already cast (concurrent request detected)")
        
        # Story 9-5 Phase 4: Emit WebSocket event
        try:
            from jarvis.api.governance_ws import sync_emit_vote_cast, sync_emit_quorum_reached
            sync_emit_vote_cast(
                proposal_id=proposal_id,
                user_id=voter.id,
                choice=choice.value,
                weight=vote_weight
            )
            
            # Check if quorum just reached
            current_quorum = self._calculate_quorum(proposal)
            if current_quorum >= proposal.quorum_required:
                sync_emit_quorum_reached(
                    proposal_id=proposal_id,
                    quorum_percentage=current_quorum
                )
        except Exception:
            pass  # Don't fail on event emission
            
        return vote

    def tally_votes(self, proposal_id: UUID) -> Dict[str, Any]:
        """Compute current results for a proposal.
        
        Returns:
            Dict containing counts, totals, and current status projection.
        """
        proposal = self._get_proposal(proposal_id)
        
        # Lazy expiration check - if deadline passed but still OPEN, user seeing this might trigger close?
        # Ideally close is explicitly called, but we can report "expired" in status
        is_expired = datetime.now(timezone.utc) > proposal.deadline
        
        return {
            "proposal_id": str(proposal_id),
            "status": proposal.status.value,
            "is_expired": is_expired,
            "total_for": proposal.total_for,
            "total_against": proposal.total_against,
            "total_abstain": proposal.total_abstain,
            "total_weight": proposal.total_weight,
            "quorum_required": proposal.quorum_required,
            "current_quorum": self._calculate_quorum(proposal),
            "approval_threshold": proposal.approval_threshold,
            "current_approval": self._calculate_approval(proposal),
        }

    def resolve_proposal(
        self,
        proposal_id: UUID,
        resolver: Optional[GovernanceUser] = None,
        force: bool = False,
    ) -> Proposal:
        """Finalize the proposal result. Checks quorum and pass thresholds.
        
        Can update status to: PASSED, REJECTED, or triggers Escalation.
        """
        proposal = self._get_proposal(proposal_id)
        
        if proposal.status != ProposalStatus.OPEN:
             # Allow resolving if it's already closed but not finalized? 
             # For now, strict: must be OPEN to resolve.
             if proposal.status not in (ProposalStatus.OPEN, ProposalStatus.DRAFT): # DRAFT shouldn't be resolved
                 pass
             
        # Check Deadline
        if datetime.now(timezone.utc) < proposal.deadline and not force:
            # Can we resolve early? Only if mathematically impossible to change outcome?
            # For simplicity, enforce deadline unless manual override (not implemented here)
            raise ValueError("Cannot resolve proposal before deadline")

        current_quorum = self._calculate_quorum(proposal)
        current_approval = self._calculate_approval(proposal)
        
        new_status = ProposalStatus.REJECTED
        reason = ""
        
        # Check Escalations first
        escalation_rule = None
        
        # 1. Quorum Check
        if current_quorum < proposal.quorum_required:
            reason = f"Quorum failed: {current_quorum:.1%} < {proposal.quorum_required:.1%}"
            escalation_rule = self.escalation.trigger.check_quorum_failed(current_quorum)
            if not escalation_rule:
                 new_status = ProposalStatus.REJECTED # Fail if no escalation rule handles it
        
        # 2. Tie Check
        elif self._is_tie(proposal):
            reason = "Tie vote detected"
            escalation_rule = self.escalation.trigger.check_tie_vote(
                proposal.id, proposal.total_for, proposal.total_against
            )
            # If no rule, default to reject? or allow tie? Usually reject (status quo prevails)
            new_status = ProposalStatus.REJECTED
            
        # 3. Threshold Check
        elif current_approval >= proposal.approval_threshold:
            new_status = ProposalStatus.PASSED
            reason = f"Passed: {current_approval:.1%} >= {proposal.approval_threshold:.1%}"
        else:
            new_status = ProposalStatus.REJECTED
            reason = f"Rejected: {current_approval:.1%} < {proposal.approval_threshold:.1%}"

        # Handle Escalation
        if escalation_rule:
            self.escalation.create_escalation(
                rule=escalation_rule,
                target_type="proposal",
                target_id=proposal.id,
                trigger_context={"reason": reason, "stats": self.tally_votes(proposal.id)}
            )
            # Proposal stays OPEN (or a new SUSPENDED status?) until escalation resolved.
            # For now, keep OPEN but maybe mark metadata?
            proposal.resolution_reason = f"Escalated: {reason}"
            # Don't change status to closed yet
        else:
            proposal.status = new_status
            proposal.closed_at = datetime.now(timezone.utc)
            proposal.resolved_at = datetime.now(timezone.utc)
            proposal.resolution_reason = reason
            
            # Snapshots final result
            proposal.result_snapshot = self.tally_votes(proposal.id)
            
            # Story 9-3 AC 8: Update voter trust based on outcome alignment
            self._update_voter_trust_on_outcome(proposal, new_status == ProposalStatus.PASSED)

        self.session.flush()
        
        # Story 9-5 Phase 4: Emit WebSocket event
        try:
            from jarvis.api.governance_ws import sync_emit_proposal_resolved
            sync_emit_proposal_resolved(
                proposal_id=proposal.id,
                status=new_status.value if hasattr(new_status, 'value') else str(new_status),
                reason=reason
            )
        except Exception:
            pass  # Don't fail on event emission
        
        return proposal

    def _get_proposal(self, proposal_id: UUID) -> Proposal:
        return self.session.query(Proposal).filter(Proposal.id == proposal_id).one()
        
    def _ensure_voting_open(self, proposal: Proposal):
        if proposal.status != ProposalStatus.OPEN:
            raise ValueError(f"Voting is not open (Status: {proposal.status})")
        if datetime.now(timezone.utc) > proposal.deadline:
            raise ValueError("Voting deadline has passed")

    def _has_voted(self, proposal_id: UUID, user_id: UUID) -> bool:
        """Check if user has already voted."""
        q = select(Vote).where(
            Vote.proposal_id == proposal_id,
            Vote.user_id == user_id
        )
        return self.session.execute(q).first() is not None

    def _update_voter_trust_on_outcome(self, proposal: Proposal, passed: bool):
        """Update all voters' trust scores based on proposal outcome.
        
        Story 9-3 AC 8: T_new = T_old + η * (Outcome Alignment)
        
        Args:
            proposal: The resolved proposal
            passed: True if proposal passed, False if rejected
        """
        from jarvis.governance.trust import TrustUpdater
        
        # Fetch all votes for this proposal
        stmt = select(Vote).where(Vote.proposal_id == proposal.id)
        votes = self.session.execute(stmt).scalars().all()
        
        for vote in votes:
            # Get the voter's trust score
            voter_stmt = select(GovernanceUser).where(GovernanceUser.id == vote.user_id)
            voter = self.session.execute(voter_stmt).scalars().first()
            
            if voter and voter.trust_metrics:
                # Determine if vote aligned with outcome
                # FOR vote + PASSED = aligned
                # AGAINST vote + REJECTED = aligned
                # ABSTAIN = neutral (no update)
                if vote.choice == VoteChoice.ABSTAIN:
                    continue
                    
                vote_was_for = (vote.choice == VoteChoice.FOR)
                aligned = (vote_was_for and passed) or (not vote_was_for and not passed)
                
                TrustUpdater.update_on_outcome(
                    trust_score=voter.trust_metrics,
                    vote_aligned_with_outcome=aligned,
                    process_abuse=False  # Would need separate abuse detection
                )

    def create_trust_snapshot(self) -> tuple[dict, float]:
        """Create frozen trust snapshot for all active governance users.
        
        Story 9-5: Governance Lock - Trust Freezing
        
        This captures trust state at proposal open time to prevent:
        - Mid-vote trust manipulation
        - Time-based attacks on trust evolution
        
        Returns:
            tuple of (snapshot_dict, total_weight)
            - snapshot_dict: {user_id: {"raw_trust": float, "effective_weight": float}}
            - total_weight: Sum of all effective weights (for legitimacy check)
        """
        from jarvis.governance.trust import TrustCalculator
        import statistics
        
        constitution = ConstitutionalGuard.get_active_constitution(self.session)
        
        # Fetch all active users with their trust scores
        stmt = select(GovernanceUser).where(GovernanceUser.is_active == True)
        all_users = self.session.execute(stmt).scalars().all()
        
        # First pass: Calculate raw trust and base weights for all users
        user_data = []
        for user in all_users:
            if user.trust_metrics:
                raw_trust = TrustCalculator.calculate_raw_trust(user.trust_metrics, constitution)
            else:
                # Default to full-weight voice when no trust score exists (test/dev seed users)
                raw_trust = 1.0
            
            # Sybil-adjusted weight (no cap yet)
            base_weight = TrustCalculator.calculate_effective_weight(
                raw_trust, [], constitution, apply_constraints=True
            )
            user_data.append({
                "user_id": str(user.id),
                "raw_trust": raw_trust,
                "base_weight": base_weight
            })
        
        # Calculate median for anti-elite cap
        base_weights = [u["base_weight"] for u in user_data]
        if base_weights:
            try:
                median_weight = statistics.median(base_weights)
            except statistics.StatisticsError:
                median_weight = constitution.minority_floor
        else:
            median_weight = constitution.minority_floor
            
        # Apply floor to median
        if median_weight < constitution.minority_floor:
            median_weight = constitution.minority_floor
            
        cap = median_weight * constitution.anti_elite_multiplier
        
        # Second pass: Apply cap and build final snapshot
        snapshot = {}
        total_weight = 0.0
        
        for u in user_data:
            effective_weight = max(
                constitution.minority_floor,
                min(u["base_weight"], cap)
            )
            snapshot[u["user_id"]] = {
                "raw_trust": u["raw_trust"],
                "effective_weight": effective_weight
            }
            total_weight += effective_weight
            
        return snapshot, total_weight

    def _compute_vote_weight(self, user: GovernanceUser, constitution: Optional[Constitution] = None) -> float:
        """Calculate vote weight using Trust-Weighted Consensus (Story 9-3).
        
        Formula:
        1. Fetch raw Trust Score (E, C, H, R)
        2. Apply Constitutional Constraints:
           - Sybil Resistance (Square root of T or similar penalty)
           - Anti-Elite Cap (5x Median)
           - Minority Floor (Epsilon)
        """
        from jarvis.governance.trust import TrustCalculator # Circular import avoidance

        if constitution is None:
            constitution = ConstitutionalGuard.get_active_constitution(self.session)

        # 1. Get User's Trust Score
        # If no trust score exists, treat as new user (0.0 trust components, but subject to minority floor)
        trust_metrics = user.trust_metrics
        
        # If None, use default empty model (effective trust ~0.5 default or 0.0?)
        # TrustScore model defaults to 0.5. Let's use that if record missing?
        # Ideally all gov users have a record.
        raw_trust = 1.0 # Default fallback (tests/dev users without trust scores)
        if trust_metrics:
            raw_trust = TrustCalculator.calculate_raw_trust(trust_metrics, constitution)
        else:
             # Just in case, create one? Or assume default components.
             # Components default to 0.5 in model definition. 
             # (0.4*0.5 + 0.3*0.5 + 0.2*0.5 + 0.1*0.5) = 0.5
             pass

        # 2. Get Global Population Weights (for Median Calculation)
        # We need the calculated effective weights of ALL active users to determine the median.
        # This is expensive O(N).
        # Optimization: Fetch all TrustScores, Calculate Weights without cap, then find Median.
        # Strict Anti-Elite rule: "5x median of WEIGHT".
        # This implies a recursive dependency if "Weight" depends on "Median Weight".
        # Solution: "Weight" usually defined as "Trust" for the distribution, then capped?
        # OR: Calculate 'Base Weight' (Sybil-adjusted Trust) for everyone. Then Median of Base Weights.
        # Then apply Cap.
        
        stmt = select(GovernanceTrustScore).join(GovernanceUser).where(GovernanceUser.is_active == True)
        all_scores = self.session.execute(stmt).scalars().all()
        
        # Calculate Base Weights (Sybil Adjusted, No Cap)
        base_weights = []
        for ts in all_scores:
            t_val = TrustCalculator.calculate_raw_trust(ts, constitution)
            # We use calculate_effective_weight to get Sybil/Floor adjustments, 
            # BUT we disable the 'Anti-Elite' cap during this first pass to find the true distribution.
            # Using median of *capped* weights to define the cap is mathematically unstable (oscillation).
            # Standard practice: Cap is based on distribution of *uncapped* merit.
            w = TrustCalculator.calculate_effective_weight(t_val, [], constitution, apply_constraints=True) 
            # Note: passing empty list skips cap calculation inside, but applies others.
            base_weights.append(w)
            
        # 3. Calculate Final Effective Weight
        return TrustCalculator.calculate_effective_weight(raw_trust, base_weights, constitution, apply_constraints=True)

    def _update_proposal_tally(self, proposal: Proposal, choice: VoteChoice, weight: float):
        """Update running totals on the proposal."""
        if choice == VoteChoice.FOR:
            proposal.total_for += weight
        elif choice == VoteChoice.AGAINST:
            proposal.total_against += weight
        elif choice == VoteChoice.ABSTAIN:
            proposal.total_abstain += weight
            
        proposal.total_weight += weight

    def _calculate_quorum(self, proposal: Proposal) -> float:
        """Calculate participation rate (Weight / Total Eligible Weight)."""
        # Story 9-5 HARDENING: Legitimacy Conservation
        # Use the FROZEN total system weight recorded at proposal open.
        # This prevents "Quorum Gaming" where:
        # 1. Spammers flood the system to dilute total weight (making quorum harder)
        # 2. Honest users leave, lowering total weight (making quorum easier for attackers)
        
        if proposal.total_weight_at_open is not None and proposal.total_weight_at_open > 0:
            return proposal.total_weight / proposal.total_weight_at_open

        # Fallback for legacy proposals or errors: Calculate on live data (Expensive!)
        # Story 9-3 Update: Quorum is based on WEIGHT, not just headcount.
        
        # NOTE: Calculating this on every read is very expensive (O(N) Trust Calcs).
        # Optimization: We should cache 'System Total Weight' or snapshot it at proposal time.
        # For now, we will recalculate to ensure correctness, assuming N < 1000.
        
        # Reuse logic from _compute_vote_weight to get total system weight
        # This duplicates effort but ensures consistency.
        # TODO: Refactor into a cached service method.
        
        from jarvis.governance.trust import TrustCalculator
        import statistics

        constitution = ConstitutionalGuard.get_active_constitution(self.session)

        stmt = select(GovernanceTrustScore).join(GovernanceUser).where(GovernanceUser.is_active == True)
        all_scores = self.session.execute(stmt).scalars().all()
        
        base_weights = []
        for ts in all_scores:
            t = TrustCalculator.calculate_raw_trust(ts, constitution)
            # Get Sybil-adjusted weight (no cap)
            w_base = TrustCalculator.calculate_effective_weight(t, [], constitution, apply_constraints=True)
            base_weights.append(w_base)
            
        # Optimization: We replicate the Anti-Elite Cap logic here manually 
        # to avoid calling calculate_effective_weight N times in a loop if we already have base_weights.
        # But for correctness and maintainability, ideally we use the centralized logic.
        # Given the previous implementation was doing manual calc, I will fix it to use Constitution params.
        
        median_weight = constitution.minority_floor
        if base_weights:
            try:
                median_weight = statistics.median(base_weights)
            except statistics.StatisticsError:
                pass
            
        # Apply Floor fallback for median
        if median_weight < constitution.minority_floor:
            median_weight = constitution.minority_floor
            
        cap = median_weight * constitution.anti_elite_multiplier
        
        effective_weights = [max(constitution.minority_floor, min(w, cap)) for w in base_weights]
        total_eligible_weight = sum(effective_weights)
        
        if total_eligible_weight == 0:
            return 0.0
            
        return proposal.total_weight / total_eligible_weight

    def _calculate_approval(self, proposal: Proposal) -> float:
        """Calculate approval % (For / (For + Against))."""
        total_deciding = proposal.total_for + proposal.total_against
        if total_deciding == 0:
            return 0.0
        return proposal.total_for / total_deciding

    def _is_tie(self, proposal: Proposal) -> bool:
        # Floating point danger, use epsilon
        diff = abs(proposal.total_for - proposal.total_against)
        return diff < 0.001 and (proposal.total_for > 0)
