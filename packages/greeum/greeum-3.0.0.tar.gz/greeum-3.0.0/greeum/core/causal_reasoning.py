"""
Greeum v2.7.0: Basic Causal Reasoning Pattern Detection System
Phase 1 Implementation - 명시적 인과관계 감지

이 모듈은 메모리 블록 간의 인과관계를 감지하고 분석하는 기본 시스템을 구현합니다.
4단계 RnD 로드맵의 Phase 1: 기본 패턴 매칭 (목표 80% 정확도)

핵심 기능:
1. 명시적 인과관계 키워드 감지 ("그래서", "때문에", "결과로" 등)
2. 시간적 선후관계 분석 (timestamp 기반)
3. 양방향 인과관계 탐지 (새 메모리 ↔ 기존 메모리)
4. 인과관계 강도 측정 (0.0-1.0 신뢰도)

설계 원칙:
- 점진적 구현: 단순한 패턴 매칭부터 시작
- 확장 가능성: Phase 2-4의 고급 기능을 위한 기반 제공
- 성능 고려: O(N) 복잡도 유지
- 다국어 지원: 한국어/영어 인과관계 표현 처리
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CausalRelationType(Enum):
    """인과관계 유형 정의"""
    CAUSE_TO_EFFECT = "cause_to_effect"      # A가 B의 원인
    EFFECT_FROM_CAUSE = "effect_from_cause"  # A가 B의 결과
    TEMPORAL_SEQUENCE = "temporal_sequence"  # 시간적 순서 관계
    CONDITIONAL = "conditional"              # 조건부 관계
    UNKNOWN = "unknown"                      # 관계 유형 불명


@dataclass
class CausalRelationship:
    """감지된 인과관계 정보"""
    source_block_id: int
    target_block_id: int
    relation_type: CausalRelationType
    confidence: float  # 0.0-1.0
    evidence: Dict[str, Any]  # 근거 정보
    detected_at: str  # ISO timestamp
    keywords_matched: List[str]
    temporal_gap_hours: Optional[float] = None


class BasicCausalDetector:
    """
    기본 인과관계 감지기 - Phase 1 구현
    
    명시적 인과관계 키워드와 시간적 패턴을 기반으로
    메모리 블록 간의 인과관계를 감지합니다.
    """
    
    def __init__(self):
        """기본 인과관계 감지기 초기화"""
        
        # 한국어 인과관계 키워드 패턴
        self.korean_causal_patterns = {
            'cause_indicators': [
                r'(?:때문에|원인으?로|인해서?|으?로 인한?)',
                r'(?:그래서|그러므로|따라서|결과적으로)',
                r'(?:덕분에|덕에|탓에|까닭에)',
                r'(?:의해|에 의해|으로부터)',
                r'(?:야기한?|초래한?|발생시킨?|유발한?)',
            ],
            'effect_indicators': [
                r'(?:결과|결과로|결과적으로)',
                r'(?:영향으?로|영향을 받아)',
                r'(?:이어서|이어져서|연이어)',
                r'(?:그래서|그러자|그러므로)',
                r'(?:따라서|에 따라)',
            ],
            'sequence_indicators': [
                r'(?:이후에?|다음에?|그 다음|나중에)',
                r'(?:먼저|우선|처음에|시작으로)',
                r'(?:그리고 나서|그 후|그 뒤)',
                r'(?:마침내|결국|최종적으로)',
            ],
            'conditional_indicators': [
                r'(?:만약|만일|혹시|경우)',
                r'(?:조건|전제|가정|상황)',
                r'(?:라면|다면|하면|면)',
            ]
        }
        
        # 영어 인과관계 키워드 패턴
        self.english_causal_patterns = {
            'cause_indicators': [
                r'(?:because of|due to|owing to|thanks to)',
                r'(?:caused by|resulted from|stemmed from)',
                r'(?:triggered by|induced by|brought about by)',
                r'(?:as a result of|in consequence of)',
            ],
            'effect_indicators': [
                r'(?:therefore|thus|hence|consequently)',
                r'(?:as a result|as a consequence)',
                r'(?:leads to|results in|causes)',
                r'(?:brings about|gives rise to|produces)',
            ],
            'sequence_indicators': [
                r'(?:after|afterwards|then|next|subsequently)',
                r'(?:first|initially|to begin with)',
                r'(?:finally|eventually|ultimately)',
                r'(?:followed by|succeeded by)',
            ],
            'conditional_indicators': [
                r'(?:if|when|whenever|provided that)',
                r'(?:in case|assuming|supposing)',
                r'(?:given that|granted that)',
            ]
        }
        
        # 시간적 임계값 (시간차이 기반 관계 탐지)
        self.temporal_thresholds = {
            'immediate': timedelta(minutes=30),    # 즉시 연관
            'short_term': timedelta(hours=6),      # 단기 연관  
            'medium_term': timedelta(days=1),      # 중기 연관
            'long_term': timedelta(days=7),        # 장기 연관
        }
        
        # 통계 정보
        self.detection_stats = {
            'total_analyzed': 0,
            'relationships_found': 0,
            'high_confidence': 0,  # >= 0.8
            'medium_confidence': 0,  # 0.5-0.8
            'low_confidence': 0,    # < 0.5
            'by_type': {t.value: 0 for t in CausalRelationType}
        }

    def detect_causal_relationships(self, new_block: Dict[str, Any], 
                                  existing_blocks: List[Dict[str, Any]]) -> List[CausalRelationship]:
        """
        새로운 메모리 블록과 기존 블록들 간의 인과관계 감지
        
        Args:
            new_block: 새로 추가된 메모리 블록
            existing_blocks: 기존 메모리 블록들
            
        Returns:
            감지된 인과관계 리스트
        """
        relationships = []
        self.detection_stats['total_analyzed'] += 1
        
        new_content = new_block.get('context', '')
        new_timestamp = datetime.fromisoformat(new_block.get('timestamp', ''))
        new_block_id = new_block.get('block_index', 0)
        
        logger.debug(f"Analyzing causal relationships for block {new_block_id}")
        
        for existing_block in existing_blocks:
            existing_content = existing_block.get('context', '')
            existing_timestamp = datetime.fromisoformat(existing_block.get('timestamp', ''))
            existing_block_id = existing_block.get('block_index', 0)
            
            # 자기 자신과의 관계는 제외
            if new_block_id == existing_block_id:
                continue
            
            # 양방향 관계 검사
            # 1. 새 블록이 기존 블록의 결과인 경우
            relationship = self._analyze_relationship(
                source_content=existing_content,
                target_content=new_content,
                source_timestamp=existing_timestamp,
                target_timestamp=new_timestamp,
                source_id=existing_block_id,
                target_id=new_block_id
            )
            
            if relationship:
                relationships.append(relationship)
                self._update_stats(relationship)
            
            # 2. 새 블록이 기존 블록의 원인인 경우 (역방향)
            reverse_relationship = self._analyze_relationship(
                source_content=new_content,
                target_content=existing_content,
                source_timestamp=new_timestamp,
                target_timestamp=existing_timestamp,
                source_id=new_block_id,
                target_id=existing_block_id
            )
            
            if reverse_relationship:
                relationships.append(reverse_relationship)
                self._update_stats(reverse_relationship)
        
        if relationships:
            self.detection_stats['relationships_found'] += len(relationships)
            logger.info(f"Found {len(relationships)} causal relationships for block {new_block_id}")
        
        return relationships

    def _analyze_relationship(self, source_content: str, target_content: str,
                            source_timestamp: datetime, target_timestamp: datetime,
                            source_id: int, target_id: int) -> Optional[CausalRelationship]:
        """
        두 메모리 블록 간의 구체적인 인과관계 분석
        
        Args:
            source_content: 원인 후보 블록의 내용
            target_content: 결과 후보 블록의 내용
            source_timestamp: 원인 블록 시간
            target_timestamp: 결과 블록 시간
            source_id: 원인 블록 ID
            target_id: 결과 블록 ID
            
        Returns:
            감지된 인과관계 또는 None
        """
        
        # 1. 언어적 패턴 분석
        linguistic_evidence = self._detect_linguistic_patterns(source_content, target_content)
        
        # 2. 시간적 관계 분석
        temporal_evidence = self._analyze_temporal_relationship(source_timestamp, target_timestamp)
        
        # 3. 종합 신뢰도 계산
        confidence = self._calculate_confidence(linguistic_evidence, temporal_evidence)
        
        # 최소 임계값 확인
        if confidence < 0.3:  # 30% 미만은 노이즈로 간주
            return None
        
        # 관계 유형 결정
        relation_type = self._determine_relation_type(linguistic_evidence, temporal_evidence)
        
        return CausalRelationship(
            source_block_id=source_id,
            target_block_id=target_id,
            relation_type=relation_type,
            confidence=confidence,
            evidence={
                'linguistic': linguistic_evidence,
                'temporal': temporal_evidence
            },
            detected_at=datetime.now().isoformat(),
            keywords_matched=linguistic_evidence.get('matched_keywords', []),
            temporal_gap_hours=temporal_evidence.get('gap_hours')
        )

    def _detect_linguistic_patterns(self, source_content: str, target_content: str) -> Dict[str, Any]:
        """
        언어적 인과관계 패턴 감지
        
        Args:
            source_content: 원인 후보 텍스트
            target_content: 결과 후보 텍스트
            
        Returns:
            언어적 증거 정보
        """
        evidence = {
            'korean_matches': [],
            'english_matches': [],
            'matched_keywords': [],
            'pattern_strength': 0.0,
            'cross_reference': False
        }
        
        combined_text = f"{source_content} {target_content}".lower()
        
        # 한국어 패턴 검사
        for pattern_type, patterns in self.korean_causal_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, combined_text)
                if matches:
                    evidence['korean_matches'].extend(matches)
                    evidence['matched_keywords'].extend(matches)
                    
                    # 패턴 유형별 가중치
                    if pattern_type == 'cause_indicators':
                        evidence['pattern_strength'] += 0.3
                    elif pattern_type == 'effect_indicators':
                        evidence['pattern_strength'] += 0.25
                    elif pattern_type == 'sequence_indicators':
                        evidence['pattern_strength'] += 0.15
                    elif pattern_type == 'conditional_indicators':
                        evidence['pattern_strength'] += 0.1
        
        # 영어 패턴 검사
        for pattern_type, patterns in self.english_causal_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                if matches:
                    evidence['english_matches'].extend(matches)
                    evidence['matched_keywords'].extend(matches)
                    
                    # 패턴 유형별 가중치
                    if pattern_type == 'cause_indicators':
                        evidence['pattern_strength'] += 0.3
                    elif pattern_type == 'effect_indicators':
                        evidence['pattern_strength'] += 0.25
                    elif pattern_type == 'sequence_indicators':
                        evidence['pattern_strength'] += 0.15
                    elif pattern_type == 'conditional_indicators':
                        evidence['pattern_strength'] += 0.1
        
        # 상호 참조 확인 (한 블록이 다른 블록을 언급)
        if self._detect_cross_reference(source_content, target_content):
            evidence['cross_reference'] = True
            evidence['pattern_strength'] += 0.2
        
        # 최대값 제한
        evidence['pattern_strength'] = min(evidence['pattern_strength'], 1.0)
        
        return evidence

    def _analyze_temporal_relationship(self, source_time: datetime, target_time: datetime) -> Dict[str, Any]:
        """
        시간적 관계 분석
        
        Args:
            source_time: 원인 블록 시간
            target_time: 결과 블록 시간
            
        Returns:
            시간적 증거 정보
        """
        time_diff = target_time - source_time
        gap_hours = abs(time_diff.total_seconds() / 3600)
        
        evidence = {
            'gap_hours': gap_hours,
            'temporal_direction': 'forward' if time_diff.total_seconds() > 0 else 'backward',
            'temporal_strength': 0.0,
            'temporal_category': 'unknown'
        }
        
        # 시간적 강도 계산 (시간 차이가 적을수록 관련성 높음)
        abs_time_diff = abs(time_diff)
        
        if abs_time_diff <= self.temporal_thresholds['immediate']:
            evidence['temporal_strength'] = 0.9
            evidence['temporal_category'] = 'immediate'
        elif abs_time_diff <= self.temporal_thresholds['short_term']:
            evidence['temporal_strength'] = 0.7
            evidence['temporal_category'] = 'short_term'
        elif abs_time_diff <= self.temporal_thresholds['medium_term']:
            evidence['temporal_strength'] = 0.5
            evidence['temporal_category'] = 'medium_term'
        elif abs_time_diff <= self.temporal_thresholds['long_term']:
            evidence['temporal_strength'] = 0.3
            evidence['temporal_category'] = 'long_term'
        else:
            evidence['temporal_strength'] = 0.1
            evidence['temporal_category'] = 'distant'
        
        # 역방향 관계는 강도 감소
        if evidence['temporal_direction'] == 'backward':
            evidence['temporal_strength'] *= 0.7
        
        return evidence

    def _detect_cross_reference(self, text1: str, text2: str) -> bool:
        """
        두 텍스트 간 상호 참조 감지
        
        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트
            
        Returns:
            상호 참조 여부
        """
        
        # 간단한 키워드 겹침 검사
        words1 = set(re.findall(r'\b\w{3,}\b', text1.lower()))
        words2 = set(re.findall(r'\b\w{3,}\b', text2.lower()))
        
        # 공통 단어가 2개 이상이고, 한 텍스트 길이의 20% 이상일 때
        common_words = words1.intersection(words2)
        if len(common_words) >= 2:
            ratio = len(common_words) / min(len(words1), len(words2))
            return ratio >= 0.2
            
        return False

    def _calculate_confidence(self, linguistic_evidence: Dict[str, Any], 
                            temporal_evidence: Dict[str, Any]) -> float:
        """
        종합 신뢰도 계산
        
        기술적 타당성 보고서의 가중치 공식 적용:
        시간적 25% + 언어적 35% + 의미적 25% + 문맥적 15%
        (현재는 Phase 1이므로 의미적/문맥적 분석은 기본값 사용)
        
        Args:
            linguistic_evidence: 언어적 증거
            temporal_evidence: 시간적 증거
            
        Returns:
            0.0-1.0 신뢰도 점수
        """
        
        # 가중치 설정
        temporal_weight = 0.25
        linguistic_weight = 0.35
        semantic_weight = 0.25    # Phase 2에서 구현 예정
        contextual_weight = 0.15  # Phase 2에서 구현 예정
        
        # 현재 구현된 요소들
        temporal_score = temporal_evidence.get('temporal_strength', 0.0)
        linguistic_score = linguistic_evidence.get('pattern_strength', 0.0)
        
        # Phase 1에서는 의미적/문맥적 점수를 기본값으로 설정
        semantic_score = 0.5 if linguistic_score > 0.3 else 0.2  # 언어 패턴 기반 추정
        contextual_score = 0.6 if linguistic_evidence.get('cross_reference', False) else 0.3
        
        # 가중 평균 계산
        confidence = (
            temporal_score * temporal_weight +
            linguistic_score * linguistic_weight +
            semantic_score * semantic_weight +
            contextual_score * contextual_weight
        )
        
        return min(confidence, 1.0)

    def _determine_relation_type(self, linguistic_evidence: Dict[str, Any], 
                               temporal_evidence: Dict[str, Any]) -> CausalRelationType:
        """
        인과관계 유형 결정
        
        Args:
            linguistic_evidence: 언어적 증거
            temporal_evidence: 시간적 증거
            
        Returns:
            인과관계 유형
        """
        
        # 조건부 키워드가 있으면 조건부 관계
        conditional_keywords = ['만약', '만일', 'if', 'when', '조건', '경우']
        matched_keywords = linguistic_evidence.get('matched_keywords', [])
        
        if any(keyword in ' '.join(matched_keywords).lower() for keyword in conditional_keywords):
            return CausalRelationType.CONDITIONAL
        
        # 원인-결과 키워드 패턴 확인
        cause_keywords = ['때문에', '원인', '인해', 'because', 'due to', 'caused by']
        effect_keywords = ['결과', '그래서', '따라서', 'therefore', 'as a result', 'consequently']
        
        has_cause_pattern = any(keyword in ' '.join(matched_keywords).lower() for keyword in cause_keywords)
        has_effect_pattern = any(keyword in ' '.join(matched_keywords).lower() for keyword in effect_keywords)
        
        if has_cause_pattern or has_effect_pattern:
            return CausalRelationType.CAUSE_TO_EFFECT
        
        # 시간적 순서만 있는 경우
        if temporal_evidence.get('temporal_direction') == 'forward':
            return CausalRelationType.TEMPORAL_SEQUENCE
        
        return CausalRelationType.UNKNOWN

    def _update_stats(self, relationship: CausalRelationship) -> None:
        """통계 정보 업데이트"""
        
        confidence = relationship.confidence
        
        if confidence >= 0.8:
            self.detection_stats['high_confidence'] += 1
        elif confidence >= 0.5:
            self.detection_stats['medium_confidence'] += 1
        else:
            self.detection_stats['low_confidence'] += 1
        
        self.detection_stats['by_type'][relationship.relation_type.value] += 1

    def get_detection_stats(self) -> Dict[str, Any]:
        """감지 통계 정보 반환"""
        
        total_relationships = self.detection_stats['relationships_found']
        
        stats = self.detection_stats.copy()
        
        if total_relationships > 0:
            stats['accuracy_estimate'] = (
                (self.detection_stats['high_confidence'] * 0.9 + 
                 self.detection_stats['medium_confidence'] * 0.7 + 
                 self.detection_stats['low_confidence'] * 0.4) / total_relationships
            )
        else:
            stats['accuracy_estimate'] = 0.0
        
        return stats


class CausalRelationshipManager:
    """
    인과관계 관리자 - 감지된 관계의 저장/조회/관리
    """
    
    def __init__(self, database_manager):
        """
        인과관계 관리자 초기화
        
        Args:
            database_manager: DatabaseManager 인스턴스
        """
        self.db_manager = database_manager
        self.detector = BasicCausalDetector()
        self._ensure_relationship_table()

    def _ensure_relationship_table(self):
        """인과관계 저장을 위한 테이블 생성"""
        
        try:
            conn = self.db_manager._get_connection()
            cursor = conn.cursor()
            
            # 인과관계 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS causal_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_block_id INTEGER NOT NULL,
                target_block_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                evidence TEXT NOT NULL,  -- JSON 형태
                detected_at TEXT NOT NULL,
                keywords_matched TEXT,   -- JSON 배열
                temporal_gap_hours REAL,
                FOREIGN KEY (source_block_id) REFERENCES blocks(block_index),
                FOREIGN KEY (target_block_id) REFERENCES blocks(block_index),
                UNIQUE(source_block_id, target_block_id, relation_type)
            )
            ''')
            
            # 인덱스 생성
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_causal_source ON causal_relationships(source_block_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_causal_target ON causal_relationships(target_block_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_causal_confidence ON causal_relationships(confidence)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_causal_type ON causal_relationships(relation_type)')
            
            conn.commit()
            logger.info("Causal relationships table initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to create causal relationships table: {e}")

    def analyze_and_store_relationships(self, new_block: Dict[str, Any], 
                                      existing_blocks: List[Dict[str, Any]]) -> List[CausalRelationship]:
        """
        새 블록에 대한 인과관계 분석 및 저장
        
        Args:
            new_block: 새로 추가된 메모리 블록
            existing_blocks: 기존 메모리 블록들
            
        Returns:
            감지된 인과관계 리스트
        """
        
        # 인과관계 감지
        relationships = self.detector.detect_causal_relationships(new_block, existing_blocks)
        
        # 데이터베이스에 저장
        stored_count = 0
        for relationship in relationships:
            if self._store_relationship(relationship):
                stored_count += 1
        
        if stored_count > 0:
            logger.info(f"Stored {stored_count} causal relationships for block {new_block.get('block_index')}")
        
        return relationships

    def _store_relationship(self, relationship: CausalRelationship) -> bool:
        """인과관계를 데이터베이스에 저장"""
        
        try:
            conn = self.db_manager._get_connection()
            cursor = conn.cursor()
            
            import json
            
            cursor.execute('''
            INSERT OR REPLACE INTO causal_relationships 
            (source_block_id, target_block_id, relation_type, confidence, evidence, 
             detected_at, keywords_matched, temporal_gap_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                relationship.source_block_id,
                relationship.target_block_id,
                relationship.relation_type.value,
                relationship.confidence,
                json.dumps(relationship.evidence),
                relationship.detected_at,
                json.dumps(relationship.keywords_matched),
                relationship.temporal_gap_hours
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to store causal relationship: {e}")
            return False

    def get_relationships_for_block(self, block_id: int) -> List[Dict[str, Any]]:
        """특정 블록과 관련된 모든 인과관계 조회"""
        
        try:
            conn = self.db_manager._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM causal_relationships 
            WHERE source_block_id = ? OR target_block_id = ?
            ORDER BY confidence DESC
            ''', (block_id, block_id))
            
            relationships = []
            for row in cursor.fetchall():
                relationships.append(dict(row))
            
            return relationships
            
        except Exception as e:
            logger.error(f"Failed to get relationships for block {block_id}: {e}")
            return []

    def get_detection_statistics(self) -> Dict[str, Any]:
        """감지 통계 및 데이터베이스 통계 조합"""
        
        detector_stats = self.detector.get_detection_stats()
        
        try:
            conn = self.db_manager._get_connection()
            cursor = conn.cursor()
            
            # 저장된 관계 수 조회
            cursor.execute('SELECT COUNT(*) FROM causal_relationships')
            total_stored = cursor.fetchone()[0]
            
            # 신뢰도별 분포
            cursor.execute('''
            SELECT 
                CASE 
                    WHEN confidence >= 0.8 THEN 'high'
                    WHEN confidence >= 0.5 THEN 'medium'
                    ELSE 'low'
                END as confidence_level,
                COUNT(*)
            FROM causal_relationships
            GROUP BY confidence_level
            ''')
            
            stored_confidence_dist = {}
            for row in cursor.fetchall():
                stored_confidence_dist[row[0]] = row[1]
            
            detector_stats.update({
                'total_stored': total_stored,
                'stored_confidence_distribution': stored_confidence_dist
            })
            
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
        
        return detector_stats