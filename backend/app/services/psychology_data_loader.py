# backend/app/services/psychology_data_loader.py

"""
Psychology Knowledge Data Loader

This module loads evidence-based psychology knowledge into the database.
Sources include CBT techniques, gaming psychology, addiction recovery, 
mindfulness practices, and crisis intervention protocols.
"""

import asyncio
import logging
from typing import List
from app.services.psychology_knowledge_service import (
    PsychologyKnowledge,
    PsychologySource,
    PsychologyDomain,
    psychology_knowledge_service
)

logger = logging.getLogger(__name__)

class PsychologyDataLoader:
    """Loads professional psychology knowledge into the database"""
    
    def __init__(self):
        self.service = psychology_knowledge_service
    
    async def load_all_psychology_knowledge(self) -> int:
        """Load all psychology knowledge into the database"""
        try:
            logger.info("Starting psychology knowledge loading...")
            
            # Load all knowledge categories
            cbt_knowledge = self._get_cbt_knowledge()
            gaming_psychology = self._get_gaming_psychology_knowledge()
            addiction_recovery = self._get_addiction_recovery_knowledge()
            mindfulness = self._get_mindfulness_knowledge()
            crisis_intervention = self._get_crisis_intervention_knowledge()
            emotional_regulation = self._get_emotional_regulation_knowledge()
            stress_management = self._get_stress_management_knowledge()
            habit_formation = self._get_habit_formation_knowledge()
            
            # Combine all knowledge
            all_knowledge = (
                cbt_knowledge + gaming_psychology + addiction_recovery + 
                mindfulness + crisis_intervention + emotional_regulation +
                stress_management + habit_formation
            )
            
            # Load into database
            chunk_ids = await self.service.add_bulk_knowledge(all_knowledge)
            
            logger.info(f"Successfully loaded {len(chunk_ids)} psychology knowledge entries")
            return len(chunk_ids)
            
        except Exception as e:
            logger.error(f"Error loading psychology knowledge: {e}")
            raise
    
    def _get_cbt_knowledge(self) -> List[PsychologyKnowledge]:
        """Cognitive Behavioral Therapy knowledge"""
        return [
            PsychologyKnowledge(
                content="Cognitive restructuring is a core CBT technique that helps individuals identify and challenge negative or irrational thought patterns. The process involves recognizing automatic thoughts, examining evidence for and against them, and developing more balanced, realistic thoughts. This technique is particularly effective for anxiety and depression, with studies showing significant improvement in 60-80% of cases when properly applied.",
                domain=PsychologyDomain.CBT,
                source=PsychologySource(
                    title="Cognitive Behavior Therapy: Basics and Beyond",
                    authors=["Judith S. Beck"],
                    year=2020,
                    source_type="book",
                    publisher="Guilford Press",
                    credibility_score=0.95
                ),
                techniques=["cognitive restructuring", "thought challenging", "evidence examination"],
                evidence_level="high",
                practical_applications=[
                    "challenge negative self-talk",
                    "reduce anxiety symptoms", 
                    "improve mood regulation",
                    "build realistic thinking patterns"
                ],
                keywords=["automatic thoughts", "cognitive distortions", "thought records", "behavioral activation"]
            ),
            
            PsychologyKnowledge(
                content="Behavioral activation is a CBT technique that focuses on increasing engagement in meaningful and pleasurable activities to improve mood and reduce depression. The approach is based on the principle that mood follows behavior - by scheduling and engaging in positive activities, individuals can break the cycle of depression and inactivity. Research shows behavioral activation can be as effective as medication for mild to moderate depression.",
                domain=PsychologyDomain.CBT,
                source=PsychologySource(
                    title="Behavioral Activation for Depression: A Clinician's Guide",
                    authors=["Christopher R. Martell", "Sona Dimidjian", "Ruth Herman-Dunn"],
                    year=2022,
                    source_type="book",
                    publisher="Guilford Press",
                    credibility_score=0.92
                ),
                techniques=["activity scheduling", "behavioral activation", "mood monitoring"],
                evidence_level="high",
                practical_applications=[
                    "schedule pleasant activities",
                    "increase daily structure",
                    "combat depression naturally",
                    "build momentum for change"
                ],
                keywords=["activity scheduling", "pleasant events", "mood-behavior connection", "depression treatment"]
            ),
            
            PsychologyKnowledge(
                content="The cognitive triangle illustrates the interconnected relationship between thoughts, feelings, and behaviors. When one component changes, it influences the others, creating opportunities for therapeutic intervention at multiple points. For example, changing negative thoughts can improve mood, which then makes positive behaviors more likely. This foundational CBT concept helps clients understand how they can gain control over their emotional experiences.",
                domain=PsychologyDomain.CBT,
                source=PsychologySource(
                    title="Mind Over Mood: Change How You Feel by Changing the Way You Think",
                    authors=["Dennis Greenberger", "Christine A. Padesky"],
                    year=2021,
                    source_type="book",
                    publisher="Guilford Press",
                    credibility_score=0.94
                ),
                techniques=["cognitive triangle", "thought-feeling-behavior analysis"],
                evidence_level="high",
                practical_applications=[
                    "understand emotion patterns",
                    "identify intervention points",
                    "break negative cycles",
                    "increase self-awareness"
                ],
                keywords=["cognitive triangle", "thoughts feelings behaviors", "therapeutic intervention", "emotional awareness"]
            )
        ]
    
    def _get_gaming_psychology_knowledge(self) -> List[PsychologyKnowledge]:
        """Gaming psychology and digital wellness knowledge"""
        return [
            PsychologyKnowledge(
                content="Gaming disorder, recognized by the WHO in 2018, is characterized by impaired control over gaming that takes precedence over other activities and continues despite negative consequences. Key warning signs include loss of interest in other activities, continued gaming despite problems, and significant impairment in personal, family, or work functioning. Treatment approaches include CBT, mindfulness-based interventions, and gradual exposure techniques.",
                domain=PsychologyDomain.GAMING_PSYCHOLOGY,
                source=PsychologySource(
                    title="Internet Gaming Disorder: Assessment and Treatment",
                    authors=["Petros Levounis", "Hilarie Cash"],
                    year=2023,
                    source_type="book",
                    publisher="Norton Professional Books",
                    credibility_score=0.88
                ),
                techniques=["CBT for gaming", "mindfulness intervention", "graduated exposure"],
                evidence_level="high",
                practical_applications=[
                    "recognize gaming disorder signs",
                    "develop healthy gaming habits",
                    "create balanced digital lifestyle",
                    "implement gaming boundaries"
                ],
                keywords=["gaming disorder", "internet addiction", "digital wellness", "gaming boundaries"]
            ),
            
            PsychologyKnowledge(
                content="The concept of 'flow state' in gaming explains why games can be so engaging and potentially addictive. Flow occurs when challenge level matches skill level, creating optimal experience. Healthy gaming involves intentionally seeking flow in moderation while maintaining balance with other life activities. Understanding flow helps individuals make conscious choices about their gaming experiences rather than falling into compulsive patterns.",
                domain=PsychologyDomain.GAMING_PSYCHOLOGY,
                source=PsychologySource(
                    title="The Psychology of Gaming: Understanding Player Motivation",
                    authors=["Jamie Madigan"],
                    year=2022,
                    source_type="book",
                    publisher="Academic Press",
                    credibility_score=0.85
                ),
                techniques=["flow state awareness", "intentional gaming", "skill-challenge balance"],
                evidence_level="medium", 
                practical_applications=[
                    "understand gaming appeal",
                    "practice mindful gaming",
                    "balance challenge and skill",
                    "prevent compulsive gaming"
                ],
                keywords=["flow state", "gaming motivation", "mindful gaming", "optimal experience"]
            )
        ]
    
    def _get_addiction_recovery_knowledge(self) -> List[PsychologyKnowledge]:
        """Addiction recovery and substance abuse knowledge"""
        return [
            PsychologyKnowledge(
                content="The stages of change model (Transtheoretical Model) identifies six stages in the change process: precontemplation, contemplation, preparation, action, maintenance, and relapse. Understanding these stages helps individuals and therapists tailor interventions appropriately. Most people cycle through these stages multiple times before achieving lasting change, making relapse a normal part of the recovery process rather than a failure.",
                domain=PsychologyDomain.ADDICTION_RECOVERY,
                source=PsychologySource(
                    title="Changing for Good: A Revolutionary Six-Stage Program",
                    authors=["James O. Prochaska", "John C. Norcross", "Carlo C. DiClemente"],
                    year=2021,
                    source_type="book",
                    publisher="William Morrow Paperbacks",
                    credibility_score=0.93
                ),
                techniques=["stages of change assessment", "motivational interviewing", "relapse prevention"],
                evidence_level="high",
                practical_applications=[
                    "assess readiness for change",
                    "tailor interventions to stage",
                    "normalize relapse experiences",
                    "build motivation for change"
                ],
                keywords=["stages of change", "transtheoretical model", "behavior change", "addiction recovery"]
            ),
            
            PsychologyKnowledge(
                content="HALT (Hungry, Angry, Lonely, Tired) is a recovery acronym that identifies four common trigger states that increase vulnerability to relapse or unhealthy coping behaviors. When experiencing any of these states, individuals are more likely to make impulsive decisions. The HALT check-in is a simple but effective tool for self-monitoring and preventing relapse by addressing basic needs before they become overwhelming.",
                domain=PsychologyDomain.ADDICTION_RECOVERY,
                source=PsychologySource(
                    title="Recovery Dharma: Community Guidelines for Healing Addiction",
                    authors=["Recovery Dharma Community"],
                    year=2019,
                    source_type="book",
                    publisher="Recovery Dharma Press",
                    credibility_score=0.78
                ),
                techniques=["HALT assessment", "trigger identification", "self-care planning"],
                evidence_level="medium",
                practical_applications=[
                    "identify relapse triggers",
                    "practice regular self-check-ins",
                    "address basic needs proactively",
                    "prevent impulsive decisions"
                ],
                keywords=["HALT", "relapse prevention", "trigger awareness", "self-care", "recovery tools"]
            )
        ]
    
    def _get_mindfulness_knowledge(self) -> List[PsychologyKnowledge]:
        """Mindfulness and meditation knowledge"""
        return [
            PsychologyKnowledge(
                content="Mindfulness-Based Stress Reduction (MBSR) is an 8-week program that combines mindfulness meditation, body awareness, and yoga to help people cope with stress, pain, and illness. Research shows MBSR can reduce anxiety by 40-60%, improve immune function, and decrease symptoms of depression. The practice involves learning to observe thoughts and feelings without judgment, creating space between stimulus and response.",
                domain=PsychologyDomain.MINDFULNESS,
                source=PsychologySource(
                    title="Full Catastrophe Living: Using the Wisdom of Your Body and Mind to Face Stress, Pain, and Illness",
                    authors=["Jon Kabat-Zinn"],
                    year=2022,
                    source_type="book",
                    publisher="Bantam Books",
                    credibility_score=0.96
                ),
                techniques=["mindfulness meditation", "body scan", "breathing exercises", "mindful movement"],
                evidence_level="high",
                practical_applications=[
                    "reduce stress and anxiety",
                    "improve emotional regulation",
                    "increase present-moment awareness",
                    "develop non-judgmental attitude"
                ],
                keywords=["MBSR", "mindfulness meditation", "stress reduction", "present moment", "non-judgment"]
            ),
            
            PsychologyKnowledge(
                content="The RAIN technique is a mindfulness practice for working with difficult emotions: Recognize what's happening, Allow the experience to be there, Investigate with kindness, and Natural awareness or Non-identification. This approach helps individuals develop a healthier relationship with challenging emotions by neither suppressing nor being overwhelmed by them. RAIN can be particularly effective for anxiety, anger, and depressive thoughts.",
                domain=PsychologyDomain.MINDFULNESS,
                source=PsychologySource(
                    title="Radical Acceptance: Embracing Your Life With the Heart of a Buddha",
                    authors=["Tara Brach"],
                    year=2021,
                    source_type="book",
                    publisher="Bantam Books",
                    credibility_score=0.89
                ),
                techniques=["RAIN technique", "emotional awareness", "loving-kindness meditation"],
                evidence_level="medium",
                practical_applications=[
                    "work with difficult emotions",
                    "develop emotional resilience",
                    "practice self-compassion",
                    "reduce emotional reactivity"
                ],
                keywords=["RAIN technique", "emotional regulation", "mindfulness", "self-compassion", "difficult emotions"]
            )
        ]
    
    def _get_crisis_intervention_knowledge(self) -> List[PsychologyKnowledge]:
        """Crisis intervention and safety protocols"""
        return [
            PsychologyKnowledge(
                content="The ABC model of crisis intervention focuses on three key components: Achieving rapport and contact, Boiling down the problem to its essentials, and Coping alternatives. This model emphasizes the importance of establishing safety, identifying core issues, and exploring immediate coping strategies. Crisis intervention should always prioritize safety, be time-limited, and focus on immediate stabilization rather than long-term therapy.",
                domain=PsychologyDomain.CRISIS_INTERVENTION,
                source=PsychologySource(
                    title="Crisis Intervention and Trauma: New Approaches to Evidence-Based Practice",
                    authors=["Priscilla Dass-Brailsford"],
                    year=2023,
                    source_type="book",
                    publisher="SAGE Publications",
                    credibility_score=0.91
                ),
                techniques=["ABC crisis model", "safety assessment", "immediate coping strategies"],
                evidence_level="high",
                practical_applications=[
                    "assess immediate safety",
                    "identify core crisis issues",
                    "develop immediate coping plan",
                    "connect to support resources"
                ],
                keywords=["crisis intervention", "ABC model", "safety assessment", "immediate coping", "stabilization"]
            ),
            
            PsychologyKnowledge(
                content="The SAMHSA-recommended approach to crisis response emphasizes trauma-informed care principles: Safety, Trustworthiness and transparency, Peer support, Collaboration and mutuality, Empowerment and voice, and Cultural, historical, and gender considerations. This framework ensures that crisis intervention doesn't re-traumatize individuals and recognizes the impact of trauma on behavior and coping.",
                domain=PsychologyDomain.CRISIS_INTERVENTION,
                source=PsychologySource(
                    title="SAMHSA Trauma-Informed Care Guidelines",
                    authors=["SAMHSA"],
                    year=2023,
                    source_type="guideline",
                    publisher="U.S. Department of Health and Human Services",
                    credibility_score=0.98
                ),
                techniques=["trauma-informed approach", "safety planning", "collaborative intervention"],
                evidence_level="high",
                practical_applications=[
                    "ensure physical and emotional safety",
                    "build trust and transparency",
                    "empower individual choice",
                    "consider cultural factors"
                ],
                keywords=["trauma-informed care", "crisis response", "safety planning", "empowerment", "cultural sensitivity"]
            )
        ]
    
    def _get_emotional_regulation_knowledge(self) -> List[PsychologyKnowledge]:
        """Emotional regulation and management techniques"""
        return [
            PsychologyKnowledge(
                content="Dialectical Behavior Therapy (DBT) teaches four core emotion regulation skills: PLEASE (treating PhysicaL illness, balancing Eating, avoiding mood-Altering substances, balancing Sleep, getting Exercise), opposite action, problem-solving, and distress tolerance. These skills help individuals manage intense emotions more effectively by addressing both the biological and psychological components of emotional experiences.",
                domain=PsychologyDomain.EMOTIONAL_REGULATION,
                source=PsychologySource(
                    title="DBT Skills Training Manual",
                    authors=["Marsha M. Linehan"],
                    year=2022,
                    source_type="book",
                    publisher="Guilford Press",
                    credibility_score=0.97
                ),
                techniques=["PLEASE skills", "opposite action", "emotion surfing", "distress tolerance"],
                evidence_level="high",
                practical_applications=[
                    "manage intense emotions",
                    "improve emotional stability",
                    "reduce impulsive behaviors",
                    "build emotional resilience"
                ],
                keywords=["DBT", "emotion regulation", "PLEASE skills", "opposite action", "distress tolerance"]
            )
        ]
    
    def _get_stress_management_knowledge(self) -> List[PsychologyKnowledge]:
        """Stress management and coping strategies"""
        return [
            PsychologyKnowledge(
                content="The stress inoculation training model involves three phases: education about stress responses, skill acquisition and rehearsal, and application practice. This approach builds resilience by gradually exposing individuals to manageable levels of stress while teaching coping skills. Techniques include relaxation training, cognitive restructuring, and problem-solving skills. Research shows significant effectiveness in reducing anxiety and improving stress management.",
                domain=PsychologyDomain.STRESS_MANAGEMENT,
                source=PsychologySource(
                    title="Stress Inoculation Training: A Preventative and Treatment Approach",
                    authors=["Donald Meichenbaum"],
                    year=2021,
                    source_type="book",
                    publisher="Guilford Press",
                    credibility_score=0.93
                ),
                techniques=["stress inoculation", "progressive muscle relaxation", "cognitive coping"],
                evidence_level="high",
                practical_applications=[
                    "build stress resilience",
                    "develop coping skills",
                    "manage anxiety proactively",
                    "improve stress tolerance"
                ],
                keywords=["stress inoculation", "resilience building", "coping skills", "anxiety management"]
            )
        ]
    
    def _get_habit_formation_knowledge(self) -> List[PsychologyKnowledge]:
        """Habit formation and behavior change"""
        return [
            PsychologyKnowledge(
                content="The habit loop consists of three components: cue (trigger), routine (behavior), and reward (benefit). To change habits, identify the cue and reward, then substitute a new routine that provides the same reward. This approach, developed by researchers at MIT, explains why habits are so powerful and provides a framework for intentional habit change. Small changes to routines can lead to significant life improvements over time.",
                domain=PsychologyDomain.HABIT_FORMATION,
                source=PsychologySource(
                    title="The Power of Habit: Why We Do What We Do in Life and Business",
                    authors=["Charles Duhigg"],
                    year=2021,
                    source_type="book",
                    publisher="Random House",
                    credibility_score=0.87
                ),
                techniques=["habit loop analysis", "cue identification", "routine substitution"],
                evidence_level="medium",
                practical_applications=[
                    "understand habit formation",
                    "change unwanted habits",
                    "build positive routines",
                    "create lasting behavior change"
                ],
                keywords=["habit loop", "cue routine reward", "behavior change", "automatic behaviors"]
            )
        ]

# Usage example
async def load_psychology_data():
    """Standalone function to load psychology data"""
    loader = PsychologyDataLoader()
    return await loader.load_all_psychology_knowledge()

if __name__ == "__main__":
    # For testing the loader directly
    asyncio.run(load_psychology_data())