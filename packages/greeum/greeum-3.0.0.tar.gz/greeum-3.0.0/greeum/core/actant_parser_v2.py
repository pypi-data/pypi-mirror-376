"""
Greeum v3.0.0: Improved Actant Parser v2
Better handling of Korean language structure
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
    
    # Metadata
    confidence: float = 0.5
    parser_version: str = "v2.0.0"
    parsed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class ImprovedActantParser:
    """
    Improved parser with better Korean language handling
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Improved entity mappings
        self.entity_mappings = {
            "user": ["사용자", "유저", "user", "고객", "클라이언트"],
            "claude": ["Claude", "claude", "AI", "assistant", "어시스턴트"],
            "team": ["팀", "개발팀", "team", "개발자들", "우리"],
            "developer": ["개발자", "developer", "엔지니어", "프로그래머"],
            "system": ["시스템", "서버", "프로그램", "애플리케이션"],
            "bug": ["버그", "bug", "오류", "에러", "error", "문제", "이슈"],
            "feature": ["기능", "feature", "피처", "함수"],
            "project": ["프로젝트", "project", "프로그램", "작업"]
        }
        
        # Improved action mappings with conjugations
        self.action_stems = {
            "요청": ["요청", "부탁", "요구", "신청"],
            "해결": ["해결", "수정", "고치", "고침", "패치", "fix"],
            "완료": ["완료", "완성", "종료", "마무리", "끝내", "끝냄"],
            "개발": ["개발", "구현", "작성", "만들", "생성", "제작"],
            "발견": ["발견", "찾", "확인", "감지", "탐지"],
            "만족": ["만족", "기뻐", "좋아"],
            "수정": ["수정", "고치", "변경", "바꾸"],
            "추가": ["추가", "더하", "붙이", "삽입"],
            "배포": ["배포", "릴리즈", "출시", "공개"],
            "실패": ["실패", "못하", "안되", "에러"],
            "성공": ["성공", "달성", "이루"],
            "받": ["받", "수령", "획득", "취득"],
            "축하": ["축하", "기념", "칭찬"],
            "제시": ["제시", "제안", "제출", "보여주"]
        }
        
        # Korean sentence endings that indicate clause boundaries
        self.clause_endings = ['고', '며', '서', '으나', '지만', '는데', '려고', '러']
    
    def parse(self, text: str, memory_id: Optional[int] = None) -> List[ActantStructure]:
        """
        Parse text into actant structures with improved Korean handling
        """
        # Remove formal endings
        text = text.replace('습니다', '다').replace('합니다', '한다')
        
        # Split into clauses
        clauses = self._split_into_clauses(text)
        
        actants = []
        for clause in clauses:
            actant = self._parse_clause(clause, memory_id)
            if actant:
                actants.append(actant)
        
        return actants
    
    def _split_into_clauses(self, text: str) -> List[str]:
        """Split text into meaningful clauses"""
        clauses = []
        current = []
        
        # Tokenize while preserving particles
        tokens = self._tokenize_korean(text)
        
        for i, token in enumerate(tokens):
            current.append(token)
            
            # Check for clause ending patterns
            for ending in self.clause_endings:
                if token.endswith(ending):
                    # Found clause boundary
                    clauses.append(' '.join(current))
                    current = []
                    break
        
        # Add remaining tokens
        if current:
            clauses.append(' '.join(current))
        
        return [c.strip() for c in clauses if c.strip()]
    
    def _tokenize_korean(self, text: str) -> List[str]:
        """Tokenize Korean text preserving particles and compound words"""
        # Keep compound nouns together
        text = text.replace('버그 수정', '버그수정')
        text = text.replace('새로운 기능', '새로운기능')
        text = text.replace('해결 방안', '해결방안')
        text = text.replace('수정 작업', '수정작업')
        
        # Split by spaces but keep particles attached
        tokens = text.split()
        return tokens
    
    def _parse_clause(self, clause: str, memory_id: Optional[int]) -> Optional[ActantStructure]:
        """Parse a single clause with improved extraction"""
        actant = ActantStructure(
            actant_id=f"act_{uuid.uuid4().hex[:12]}",
            memory_id=memory_id
        )
        
        # Extract components in order
        subject, clause_remain = self._extract_subject_v2(clause)
        if subject:
            actant.subject_raw = subject
            actant.subject_hash = self._get_entity_hash(subject)
        
        # Extract object before action (Korean word order)
        obj, clause_remain = self._extract_object_v2(clause_remain if clause_remain else clause)
        if obj:
            actant.object_raw = obj
            actant.object_hash = self._get_entity_hash(obj)
        
        # Extract action last
        action = self._extract_action_v2(clause_remain if clause_remain else clause)
        if action:
            actant.action_raw = action
            actant.action_hash = self._get_action_hash(action)
        
        # Calculate confidence
        actant.confidence = self._calculate_confidence(actant)
        
        if actant.subject_raw or actant.action_raw or actant.object_raw:
            return actant
        return None
    
    def _extract_subject_v2(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract subject with compound noun support"""
        # Pattern: (word+)이/가/은/는/께서
        patterns = [
            r'^([\w\s]+?)(?:이|가|은|는|께서)\s+(.+)$',
            r'^([\w]+?)(?:이|가|은|는|께서)\s+(.+)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text)
            if match:
                subject = match.group(1).strip()
                remainder = match.group(2).strip()
                
                # Restore compound words
                subject = subject.replace('버그수정', '버그 수정')
                subject = subject.replace('새로운기능', '새로운 기능')
                
                return subject, remainder
        
        # Check for known entities at start
        for entity, variations in self.entity_mappings.items():
            for var in variations:
                if text.startswith(var):
                    remainder = text[len(var):].strip()
                    return var, remainder
        
        return None, text
    
    def _extract_object_v2(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract object with compound noun support"""
        # Pattern: (word+)을/를/에게/한테
        patterns = [
            r'([\w\s]+?)(?:을|를|에게|한테)\s+(.+)$',
            r'([\w]+?)(?:을|를|에게|한테)\s+(.+)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                obj = match.group(1).strip()
                remainder = match.group(2).strip()
                
                # Restore compound words
                obj = obj.replace('버그수정', '버그 수정')
                obj = obj.replace('새로운기능', '새로운 기능')
                obj = obj.replace('해결방안', '해결 방안')
                
                return obj, remainder
        
        return None, text
    
    def _extract_action_v2(self, text: str) -> Optional[str]:
        """Extract action with better verb stem detection"""
        # Korean verb patterns with various endings
        verb_patterns = [
            r'(\w+?)(?:했|한|하여|하고|했고|했다|한다|합니다)',
            r'(\w+?)(?:됐|된|되어|되고|됐다|된다|됩니다)',
            r'(\w+?)(?:였|인|이고|였다|입니다)',
            r'(\w+?)(?:았|안|아서|았다)',
            r'(\w+?)(?:었|언|어서|었다)'
        ]
        
        for pattern in verb_patterns:
            match = re.search(pattern, text)
            if match:
                stem = match.group(1)
                
                # Check if it's a known action
                for action_key, variations in self.action_stems.items():
                    if stem in variations:
                        return action_key
                
                # Return the stem itself
                return stem
        
        # Check for action nouns (명사형 동사)
        for action_key, variations in self.action_stems.items():
            for var in variations:
                if var in text:
                    return action_key
        
        return None
    
    def _get_entity_hash(self, entity: str) -> str:
        """Get normalized entity hash"""
        entity_lower = entity.lower()
        
        # Check known mappings
        for key, variations in self.entity_mappings.items():
            if entity in variations or entity_lower in [v.lower() for v in variations]:
                return key
        
        # Create new hash
        return hashlib.md5(f"entity_{entity_lower}".encode()).hexdigest()[:8]
    
    def _get_action_hash(self, action: str) -> str:
        """Get normalized action hash"""
        action_lower = action.lower()
        
        # Check known mappings
        for key, variations in self.action_stems.items():
            if action in variations or action == key:
                return key
        
        # Create new hash
        return hashlib.md5(f"action_{action_lower}".encode()).hexdigest()[:8]
    
    def _calculate_confidence(self, actant: ActantStructure) -> float:
        """Calculate parsing confidence"""
        confidence = 0.0
        
        # Having all three components
        if actant.subject_raw:
            confidence += 0.35
        if actant.action_raw:
            confidence += 0.35
        if actant.object_raw:
            confidence += 0.30
        
        return min(1.0, confidence)