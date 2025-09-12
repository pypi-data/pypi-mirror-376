"""
Greeum v3.0.0: Actant Parser
Parses memory text into Greimas actant model structure
"""

import re
import uuid
import json
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ActantStructure:
    """Represents a parsed actant structure"""
    actant_id: str
    memory_id: Optional[int] = None
    
    # Primary actants
    subject_raw: Optional[str] = None
    subject_hash: Optional[str] = None
    action_raw: Optional[str] = None
    action_hash: Optional[str] = None
    object_raw: Optional[str] = None
    object_hash: Optional[str] = None
    
    # Secondary actants
    sender_raw: Optional[str] = None
    sender_hash: Optional[str] = None
    receiver_raw: Optional[str] = None
    receiver_hash: Optional[str] = None
    helper_raw: Optional[str] = None
    helper_hash: Optional[str] = None
    opponent_raw: Optional[str] = None
    opponent_hash: Optional[str] = None
    
    # Metadata
    confidence: float = 0.5
    parser_version: str = "v3.0.0"
    parsed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class ActantParser:
    """
    Parses memory text into actant structures
    Uses rule-based parsing with entity normalization
    """
    
    def __init__(self, db_manager):
        """
        Initialize actant parser
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        
        # Entity mappings (will be loaded from DB)
        self.entity_mappings = {
            "user": ["사용자", "유저", "user", "고객", "클라이언트", "client"],
            "claude": ["Claude", "claude", "AI", "assistant", "어시스턴트", "봇"],
            "team": ["팀", "개발팀", "team", "개발자들", "엔지니어들", "우리"],
            "system": ["시스템", "서버", "프로그램", "애플리케이션", "앱"],
            "project": ["프로젝트", "project", "작업", "과제", "일"],
            "bug": ["버그", "bug", "오류", "에러", "error", "문제", "이슈"],
            "feature": ["기능", "feature", "피처", "특징", "함수"]
        }
        
        # Action mappings
        self.action_mappings = {
            "request": ["요청", "부탁", "요구", "신청", "request", "ask", "demand"],
            "complete": ["완료", "완성", "종료", "마무리", "complete", "finish", "done"],
            "create": ["생성", "만들기", "작성", "개발", "구현", "create", "make", "build"],
            "fix": ["수정", "고치기", "해결", "패치", "fix", "solve", "resolve"],
            "analyze": ["분석", "검토", "조사", "파악", "analyze", "review", "examine"],
            "update": ["업데이트", "갱신", "변경", "수정", "update", "change", "modify"],
            "delete": ["삭제", "제거", "지우기", "delete", "remove", "clear"]
        }
        
        # Korean verb patterns
        self.korean_verb_patterns = [
            r'(\w+)했다', r'(\w+)했어', r'(\w+)했음',
            r'(\w+)한다', r'(\w+)하고', r'(\w+)하여',
            r'(\w+)됐다', r'(\w+)된다', r'(\w+)되어'
        ]
        
        self._load_entity_mappings()
    
    def _load_entity_mappings(self):
        """Load entity and action mappings from database"""
        try:
            cursor = self.db_manager.conn.cursor()
            
            # Load entities
            cursor.execute("SELECT entity_hash, variations FROM actant_entities")
            for row in cursor.fetchall():
                if row['variations']:
                    variations = json.loads(row['variations'])
                    self.entity_mappings[row['entity_hash']] = variations
            
            # Load actions
            cursor.execute("SELECT action_hash, variations FROM actant_actions")
            for row in cursor.fetchall():
                if row['variations']:
                    variations = json.loads(row['variations'])
                    self.action_mappings[row['action_hash']] = variations
            
        except Exception as e:
            logger.debug(f"Loading mappings (expected on first run): {e}")
    
    def parse(self, text: str, memory_id: Optional[int] = None) -> List[ActantStructure]:
        """
        Parse text into actant structures
        
        Args:
            text: Memory text to parse
            memory_id: Associated memory block ID
            
        Returns:
            List of parsed actant structures
        """
        actants = []
        
        # Split by conjunctions to find multiple actants
        segments = self._split_by_conjunctions(text)
        
        for segment in segments:
            actant = self._parse_segment(segment, memory_id)
            if actant:
                actants.append(actant)
        
        # Find relations between actants
        if len(actants) > 1:
            self._infer_relations(actants)
        
        return actants
    
    def _split_by_conjunctions(self, text: str) -> List[str]:
        """Split text by conjunctions to find multiple clauses"""
        # Korean conjunctions
        korean_conj = ['그리고', '그래서', '하지만', '그러나', '따라서', '이후', '그후']
        
        # Split by various patterns
        segments = [text]
        
        # Split by Korean conjunctions
        for conj in korean_conj:
            new_segments = []
            for segment in segments:
                parts = segment.split(conj)
                new_segments.extend(parts)
            segments = new_segments
        
        # Split by punctuation
        final_segments = []
        for segment in segments:
            # Split by comma if it separates clauses
            if ',' in segment:
                parts = segment.split(',')
                final_segments.extend(parts)
            else:
                final_segments.append(segment)
        
        # Clean segments
        final_segments = [s.strip() for s in final_segments if s.strip()]
        
        return final_segments
    
    def _parse_segment(self, segment: str, memory_id: Optional[int]) -> Optional[ActantStructure]:
        """Parse a single segment into actant structure"""
        actant = ActantStructure(
            actant_id=f"act_{uuid.uuid4().hex[:12]}",
            memory_id=memory_id
        )
        
        # Extract subject
        subject = self._extract_subject(segment)
        if subject:
            actant.subject_raw = subject
            actant.subject_hash = self._get_entity_hash(subject, 'subject')
        
        # Extract action
        action = self._extract_action(segment)
        if action:
            actant.action_raw = action
            actant.action_hash = self._get_action_hash(action)
        
        # Extract object
        obj = self._extract_object(segment, subject, action)
        if obj:
            actant.object_raw = obj
            actant.object_hash = self._get_entity_hash(obj, 'object')
        
        # Calculate confidence
        actant.confidence = self._calculate_confidence(actant)
        
        # Only return if we have at least subject or action
        if actant.subject_raw or actant.action_raw:
            return actant
        
        return None
    
    def _extract_subject(self, text: str) -> Optional[str]:
        """Extract subject from text"""
        # Korean subject markers
        subject_markers = ['이', '가', '은', '는', '께서']
        
        for marker in subject_markers:
            pattern = rf'(\w+){marker}\s'
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # Check known entities at start
        words = text.split()
        if words:
            first_word = words[0]
            for entity_key, variations in self.entity_mappings.items():
                if first_word.lower() in [v.lower() for v in variations]:
                    return first_word
        
        # Implicit subject (common in Korean)
        return None
    
    def _extract_action(self, text: str) -> Optional[str]:
        """Extract action from text"""
        # Try Korean verb patterns
        for pattern in self.korean_verb_patterns:
            match = re.search(pattern, text)
            if match:
                verb_stem = match.group(1)
                # Check if it's a known action
                for action_key, variations in self.action_mappings.items():
                    if verb_stem in variations or f"{verb_stem}하다" in variations:
                        return verb_stem
                return verb_stem
        
        # Try English patterns
        english_verbs = re.findall(r'\b(request|create|update|delete|fix|solve|complete)\w*\b', text.lower())
        if english_verbs:
            return english_verbs[0]
        
        return None
    
    def _extract_object(self, text: str, subject: Optional[str], action: Optional[str]) -> Optional[str]:
        """Extract object from text"""
        # Korean object markers
        object_markers = ['을', '를', '에게', '한테', '께']
        
        for marker in object_markers:
            pattern = rf'(\w+){marker}\s'
            matches = re.findall(pattern, text)
            for match in matches:
                # Skip if it's the subject
                if match != subject:
                    return match
        
        # If we have action, look for words after it
        if action:
            pattern = rf'{action}\w*\s+(\w+)'
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # Look for known entities
        words = text.split()
        for word in words:
            if word != subject and word != action:
                for entity_key, variations in self.entity_mappings.items():
                    if word.lower() in [v.lower() for v in variations]:
                        return word
        
        return None
    
    def _get_entity_hash(self, entity: str, entity_type: str) -> str:
        """Get or create entity hash"""
        entity_lower = entity.lower()
        
        # Check existing mappings
        for hash_key, variations in self.entity_mappings.items():
            if entity_lower in [v.lower() for v in variations]:
                self._update_entity_occurrence(hash_key, entity)
                return hash_key
        
        # Create new entity
        entity_hash = hashlib.md5(f"{entity_type}_{entity_lower}".encode()).hexdigest()[:8]
        self._create_entity(entity_hash, entity, entity_type)
        
        return entity_hash
    
    def _get_action_hash(self, action: str) -> str:
        """Get or create action hash"""
        action_lower = action.lower()
        
        # Check existing mappings
        for hash_key, variations in self.action_mappings.items():
            if action_lower in [v.lower() for v in variations]:
                self._update_action_occurrence(hash_key, action)
                return hash_key
        
        # Create new action
        action_hash = hashlib.md5(f"action_{action_lower}".encode()).hexdigest()[:8]
        self._create_action(action_hash, action)
        
        return action_hash
    
    def _calculate_confidence(self, actant: ActantStructure) -> float:
        """Calculate parsing confidence"""
        confidence = 0.0
        
        # Base confidence for having components
        if actant.subject_raw:
            confidence += 0.3
        if actant.action_raw:
            confidence += 0.3
        if actant.object_raw:
            confidence += 0.2
        
        # Bonus for known entities/actions
        if actant.subject_hash in self.entity_mappings:
            confidence += 0.1
        if actant.action_hash in self.action_mappings:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _infer_relations(self, actants: List[ActantStructure]):
        """Infer relations between actants"""
        for i, actant1 in enumerate(actants):
            for actant2 in actants[i+1:]:
                # Object-Subject chain
                if actant1.object_hash and actant1.object_hash == actant2.subject_hash:
                    actant2.sender_raw = actant1.subject_raw
                    actant2.sender_hash = actant1.subject_hash
                
                # Same subject sequential
                if actant1.subject_hash and actant1.subject_hash == actant2.subject_hash:
                    # Sequential actions by same subject
                    actant2.metadata['previous_action'] = actant1.action_raw
    
    def _create_entity(self, entity_hash: str, entity: str, entity_type: str):
        """Create new entity in database"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO actant_entities
            (entity_hash, entity_type, canonical_form, variations, 
             first_seen, last_seen, occurrence_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entity_hash,
            entity_type,
            entity,
            json.dumps([entity]),
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            1,
            '{}'
        ))
        self.db_manager.conn.commit()
        
        # Update in-memory mapping
        self.entity_mappings[entity_hash] = [entity]
    
    def _create_action(self, action_hash: str, action: str):
        """Create new action in database"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO actant_actions
            (action_hash, action_type, canonical_form, variations,
             first_seen, last_seen, occurrence_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            action_hash,
            'unknown',  # Will be classified later
            action,
            json.dumps([action]),
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            1,
            '{}'
        ))
        self.db_manager.conn.commit()
        
        # Update in-memory mapping
        self.action_mappings[action_hash] = [action]
    
    def _update_entity_occurrence(self, entity_hash: str, variation: str):
        """Update entity occurrence count and variations"""
        cursor = self.db_manager.conn.cursor()
        
        # Get current variations
        cursor.execute('SELECT variations FROM actant_entities WHERE entity_hash = ?', (entity_hash,))
        row = cursor.fetchone()
        if row:
            variations = json.loads(row['variations']) if row['variations'] else []
            if variation not in variations:
                variations.append(variation)
            
            cursor.execute('''
                UPDATE actant_entities 
                SET occurrence_count = occurrence_count + 1,
                    last_seen = ?,
                    variations = ?
                WHERE entity_hash = ?
            ''', (datetime.now().isoformat(), json.dumps(variations), entity_hash))
            self.db_manager.conn.commit()
    
    def _update_action_occurrence(self, action_hash: str, variation: str):
        """Update action occurrence count and variations"""
        cursor = self.db_manager.conn.cursor()
        
        # Get current variations
        cursor.execute('SELECT variations FROM actant_actions WHERE action_hash = ?', (action_hash,))
        row = cursor.fetchone()
        if row:
            variations = json.loads(row['variations']) if row['variations'] else []
            if variation not in variations:
                variations.append(variation)
            
            cursor.execute('''
                UPDATE actant_actions
                SET occurrence_count = occurrence_count + 1,
                    last_seen = ?,
                    variations = ?
                WHERE action_hash = ?
            ''', (datetime.now().isoformat(), json.dumps(variations), action_hash))
            self.db_manager.conn.commit()
    
    def save_actant(self, actant: ActantStructure):
        """Save actant structure to database"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO memory_actants
            (actant_id, memory_id, subject_raw, subject_hash, action_raw, action_hash,
             object_raw, object_hash, sender_raw, sender_hash, receiver_raw, receiver_hash,
             helper_raw, helper_hash, opponent_raw, opponent_hash,
             confidence, parser_version, parsed_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            actant.actant_id, actant.memory_id,
            actant.subject_raw, actant.subject_hash,
            actant.action_raw, actant.action_hash,
            actant.object_raw, actant.object_hash,
            actant.sender_raw, actant.sender_hash,
            actant.receiver_raw, actant.receiver_hash,
            actant.helper_raw, actant.helper_hash,
            actant.opponent_raw, actant.opponent_hash,
            actant.confidence, actant.parser_version,
            actant.parsed_at, json.dumps(actant.metadata)
        ))
        self.db_manager.conn.commit()
    
    def get_entity_stats(self) -> Dict[str, Any]:
        """Get entity statistics"""
        cursor = self.db_manager.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM actant_entities')
        total_entities = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM actant_actions')
        total_actions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM memory_actants')
        total_actants = cursor.fetchone()[0]
        
        return {
            'total_entities': total_entities,
            'total_actions': total_actions,
            'total_actants': total_actants,
            'entity_types': self._count_entity_types(),
            'action_types': self._count_action_types()
        }
    
    def _count_entity_types(self) -> Dict[str, int]:
        """Count entities by type"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute('SELECT entity_type, COUNT(*) FROM actant_entities GROUP BY entity_type')
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def _count_action_types(self) -> Dict[str, int]:
        """Count actions by type"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute('SELECT action_type, COUNT(*) FROM actant_actions GROUP BY action_type')
        return {row[0]: row[1] for row in cursor.fetchall()}