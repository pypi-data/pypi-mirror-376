import os
import json
import hashlib
import datetime
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
from .database_manager import DatabaseManager
# from .causal_reasoning import CausalRelationshipManager  # Removed for v3.0.0 simplification
import logging

logger = logging.getLogger(__name__)

class BlockManager:
    """장기 기억 블록을 관리하는 클래스 (DatabaseManager 사용)"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """BlockManager 초기화
        Args:
            db_manager: DatabaseManager (없으면 기본 SQLite 파일 생성)
        """
        self.db_manager = db_manager or DatabaseManager()
        
        # v2.7.0: Initialize causal reasoning system (disabled for v3.0 stability)
        self.causal_manager = None
        logger.debug("Causal reasoning disabled for v3.0 release")
        
        # v3.0.0: GraphIndex 통합 - 고성능 그래프 기반 검색
        try:
            from ..graph.index import GraphIndex
            self.graph_index = GraphIndex()
            self._auto_bootstrap_graph_index()
            logger.info("GraphIndex integrated successfully")
        except ImportError as e:
            logger.warning(f"GraphIndex not available: {e}")
            self.graph_index = None
        except Exception as e:
            logger.error(f"GraphIndex initialization failed: {e}")
            self.graph_index = None
        
        # 메트릭 추적 (관측성 개선)
        self.metrics = {
            'total_searches': 0,
            'graph_searches': 0,
            'graph_hits': 0,
            'fallback_searches': 0,
            'total_hops': 0,
            'search_count': 0,
            'avg_response_time': 0.0,
            'local_hit_rate': 0.0,
            'avg_hops': 0.0
        }
        
    def _compute_hash(self, block_data: Dict[str, Any]) -> str:
        """블록의 해시값 계산. 해시 계산에 포함되지 않아야 할 필드는 이 함수 호출 전에 정리되어야 함."""
        block_copy = block_data.copy()
        block_copy.pop('hash', None)
        block_str = json.dumps(block_copy, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(block_str.encode('utf-8')).hexdigest()
    
    def add_block(self, context: str, keywords: List[str], tags: List[str], 
                 embedding: List[float], importance: float, 
                 metadata: Optional[Dict[str, Any]] = None,
                 embedding_model: Optional[str] = 'default') -> Optional[Dict[str, Any]]:
        """
        새 블록 추가 (DatabaseManager 사용)
        """
        import time
        write_start_time = time.time()
        
        logger.debug(f"add_block called: context='{context[:20]}...'")
        last_block_info = self.db_manager.get_last_block_info()
        
        new_block_index: int
        prev_h: str

        if last_block_info:
            new_block_index = last_block_info.get('block_index', -1) + 1
            prev_h = last_block_info.get('hash', '')
        else:
            new_block_index = 0
            prev_h = ''
        
        current_timestamp = datetime.datetime.now().isoformat()
        
        # 해시 계산 대상이 되는 핵심 블록 데이터 구성
        # keywords, tags, embedding, metadata 등은 별도 테이블 관리되므로 해시 대상에서 제외 (설계 결정 사항)
        block_data_for_hash = {
            "block_index": new_block_index,
            "timestamp": current_timestamp,
            "context": context,
            "importance": importance,
            "prev_hash": prev_h,
        }
        current_hash = self._compute_hash(block_data_for_hash)

        # M2: Add optional links.neighbors cache for anchor-based graph system
        links = {}
        if metadata and 'links' in metadata:
            links = metadata['links']
        
        # v2.4.0a2: 액탄트 분석 정보 자동 추가
        enhanced_metadata = self._enhance_metadata_with_actants(context, metadata or {})
        
        block_to_store_in_db = {
            "block_index": new_block_index,
            "timestamp": current_timestamp,
            "context": context,
            "keywords": keywords,
            "tags": tags,
            "embedding": embedding,
            "importance": importance,
            "hash": current_hash,
            "prev_hash": prev_h,
            "metadata": enhanced_metadata,
            "embedding_model": embedding_model,
            "links": links  # M2: Store neighbor links cache
        }
        
        try:
            added_idx = self.db_manager.add_block(block_to_store_in_db)
            # add_block이 실제 추가된 블록의 index를 반환한다고 가정 (DB auto-increment 시 유용)
            # 현재 DatabaseManager.add_block은 전달된 block_data.get('block_index')를 사용하므로, added_idx는 new_block_index와 같음.
            added_block = self.db_manager.get_block(new_block_index)
            
            # v2.7.0: Analyze causal relationships after successful block addition
            if self.causal_manager and added_block:
                try:
                    # Get recent blocks for causal analysis (limit to avoid performance issues)
                    recent_blocks = self.get_blocks(limit=50, sort_by='timestamp', order='desc')  
                    relationships = self.causal_manager.analyze_and_store_relationships(
                        added_block, recent_blocks
                    )
                    
                    if relationships:
                        logger.info(f"Detected {len(relationships)} causal relationships for block {new_block_index}")
                        # Update metadata with causal relationship count
                        enhanced_metadata['causal_relationships_count'] = len(relationships)
                        
                except Exception as causal_error:
                    logger.warning(f"Causal analysis failed for block {new_block_index}: {causal_error}")
            
            # Near-Anchor Write: 활성 앵커 주변에 링크 형성
            links_created = self._update_near_anchor_links(new_block_index, enhanced_metadata)
            
            # 메트릭 수집
            write_end_time = time.time()
            latency_ms = (write_end_time - write_start_time) * 1000
            
            try:
                from ..core.metrics_collector import MetricsCollector, WriteMetric
                collector = MetricsCollector()
                
                # 앵커 근처 쓰기 여부 확인
                near_anchor = links_created > 0
                
                metric = WriteMetric(
                    timestamp=datetime.datetime.now(),
                    block_index=new_block_index,
                    near_anchor=near_anchor,
                    links_created=links_created,
                    latency_ms=latency_ms,
                    metadata=enhanced_metadata
                )
                collector.record_write(metric)
                logger.debug(f"Write metric recorded: block={new_block_index}, links={links_created}, latency={latency_ms:.1f}ms")
            except ImportError:
                logger.debug("MetricsCollector not available")
            except Exception as e:
                logger.debug(f"Failed to record write metric: {e}")
            
            logger.info(f"Block added successfully: index={new_block_index}, hash={current_hash[:10]}...")
            # Return just the block_index instead of the full block dict
            return new_block_index
        except Exception as e:
            logger.error(f"BlockManager: Error adding block to DB - {e}", exc_info=True)
            return None
    
    def get_blocks(self, start_idx: Optional[int] = None, end_idx: Optional[int] = None,
                     limit: int = 100, offset: int = 0, 
                     sort_by: str = 'block_index', order: str = 'asc') -> List[Dict[str, Any]]:
        """블록 범위 조회 (DatabaseManager 사용)"""
        logger.debug(f"get_blocks called: start={start_idx}, end={end_idx}, limit={limit}, offset={offset}, sort_by={sort_by}, order={order}")
        blocks = self.db_manager.get_blocks(start_idx=start_idx, end_idx=end_idx, limit=limit, offset=offset, sort_by=sort_by, order=order)
        logger.debug(f"get_blocks result: {len(blocks)} blocks returned")
        return blocks
    
    def _enhance_metadata_with_actants(self, context: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """v2.4.0a2: 메타데이터에 액탄트 분석 정보 추가 (그레마스 6개 액탄트 역할 분석)"""
        
        # 기존 메타데이터 보존
        enhanced_metadata = metadata.copy()
        
        # 이미 액탄트 분석이 있으면 건너뛰기
        if "actant_analysis" in enhanced_metadata:
            return enhanced_metadata
        
        # 그레마스 6개 액탄트 역할 분석
        actants = {}
        
        # Subject (주체) - 행동의 주체, 묵시적 화자 포함
        subject_patterns = ["나는", "내가", "우리가", "팀이", "사용자가"]
        subject_found = False
        for pattern in subject_patterns:
            if pattern in context:
                actants["subject"] = {
                    "entity": pattern.replace("는", "").replace("가", ""),
                    "confidence": 0.8,
                    "extraction_method": "explicit_pattern"
                }
                subject_found = True
                break
        
        # 묵시적 주체 (1인칭 동사 활용형 감지)
        if not subject_found and any(word in context for word in ["했고", "했다", "했어요", "시작했", "느껴요", "생각해"]):
            actants["subject"] = {
                "entity": "화자",
                "confidence": 0.7,
                "extraction_method": "implicit_first_person"
            }
        
        # Object (객체) - 추구하거나 획득하려는 대상
        object_patterns = ["프로젝트", "작업", "기능", "문제", "목표", "결과", "경험", "기회"]
        for pattern in object_patterns:
            if pattern in context:
                # 수식어가 있는 경우 함께 추출 (예: "AI 프로젝트")
                words = context.split()
                for i, word in enumerate(words):
                    if pattern in word:
                        if i > 0 and words[i-1] not in ["는", "가", "을", "를", "의"]:
                            combined = f"{words[i-1]} {pattern}"
                        else:
                            combined = pattern
                        actants["object"] = {
                            "entity": combined,
                            "confidence": 0.8,
                            "extraction_method": "contextual_extraction"
                        }
                        break
                break
        
        # Sender (발신자) - 목표를 부여하거나 동기를 제공하는 존재
        if any(word in context for word in ["해야", "요청", "지시", "부탁"]):
            actants["sender"] = {
                "entity": "외부 요청자",
                "confidence": 0.6,
                "extraction_method": "obligation_pattern"
            }
        elif actants.get("subject", {}).get("entity") in ["화자", "나"]:
            actants["sender"] = {
                "entity": "자기동기",
                "confidence": 0.7,
                "extraction_method": "self_motivation"
            }
        
        # Receiver (수신자) - 목표 달성의 수혜자
        if actants.get("subject"):
            actants["receiver"] = {
                "entity": actants["subject"]["entity"],
                "confidence": 0.7,
                "extraction_method": "subject_beneficiary"
            }
        
        # Helper (조력자) - 목표 달성을 돕는 요소
        helper_patterns = ["도구", "기술", "팀", "지원", "도움", "흥미", "동기", "열정"]
        for pattern in helper_patterns:
            if pattern in context or (pattern == "흥미" and "흥미로" in context):
                actants["helper"] = {
                    "entity": pattern if pattern in context else "흥미",
                    "confidence": 0.6,
                    "extraction_method": "supportive_element"
                }
                break
        
        # Opponent (적대자) - 목표 달성을 방해하는 요소
        opponent_patterns = ["문제", "어려움", "장애물", "실패", "걱정", "우려"]
        for pattern in opponent_patterns:
            if pattern in context:
                actants["opponent"] = {
                    "entity": pattern,
                    "confidence": 0.7,
                    "extraction_method": "obstacle_detection"
                }
                break
        
        # 서사 패턴 추론 (더 정밀한 분류)
        narrative_pattern = "other"
        if any(word in context for word in ["시작했", "새로운", "처음"]):
            narrative_pattern = "initiation"  # 개시/시작
        elif any(word in context for word in ["시작", "계획", "목표"]) and not any(word in context for word in ["시작했"]):
            narrative_pattern = "quest"  # 탐구/추구
        elif any(word in context for word in ["문제", "어려움", "실패", "걱정"]):
            narrative_pattern = "conflict"  # 갈등
        elif any(word in context for word in ["완료", "성공", "달성", "해결"]):
            narrative_pattern = "acquisition"  # 획득/완성
        elif any(word in context for word in ["흥미로", "좋아", "만족", "기뻐"]):
            narrative_pattern = "satisfaction"  # 만족/긍정
        
        # 액탄트 분석 정보 추가
        enhanced_metadata["actant_analysis"] = {
            "actants": actants,
            "narrative_pattern": narrative_pattern,
            "action_sequence": [],
            "analysis_quality": {
                "actant_count": len(actants),
                "quality_level": "medium" if len(actants) > 0 else "low"
            },
            "analysis_timestamp": datetime.datetime.now().isoformat(),
            "analysis_method": "pattern_matching_v240a2"
        }
        
        # 처리 정보 추가
        enhanced_metadata["actant_processing"] = {
            "version": "2.4.0a2",
            "processed_at": datetime.datetime.now().isoformat(),
            "auto_generated": True
        }
        
        return enhanced_metadata
    
    def get_block_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """인덱스로 블록 조회 (DatabaseManager 사용)"""
        return self.db_manager.get_block(index)
    
    def verify_blocks(self) -> bool:
        """블록체인 무결성 검증 (DatabaseManager 사용). prev_hash 연결 및 개별 해시 (단순화된 방식) 검증."""
        logger.debug("verify_blocks called")
        all_blocks = self.get_blocks(limit=100000, sort_by='block_index', order='asc')
        if not all_blocks:
            logger.info("No blocks to verify, returning True for integrity")
            return True

        for i, block in enumerate(all_blocks):
            if i > 0:
                if block.get('prev_hash') != all_blocks[i-1].get('hash'):
                    logger.warning(f"BlockManager: prev_hash mismatch! index {i}, block_hash {block.get('hash')}, prev_expected {all_blocks[i-1].get('hash')}, prev_actual {block.get('prev_hash')}")
                    return False
            
            # 개별 블록 해시 검증
            # 저장 시 해시된 필드와 동일한 필드로 재계산하여 비교해야 함.
            # 현재 add_block에서 block_data_for_hash 기준으로 해시했으므로, 동일하게 구성하여 비교.
            expected_data_for_hash = {
                "block_index": block.get('block_index'),
                "timestamp": block.get('timestamp'),
                "context": block.get('context'),
                "importance": block.get('importance'),
                "prev_hash": block.get('prev_hash'),
            }
            recalculated_hash = self._compute_hash(expected_data_for_hash)
            if recalculated_hash != block.get('hash'):
                logger.warning(f"BlockManager: Hash mismatch! block_index {block.get('block_index')}. Recalculated: {recalculated_hash}, Stored: {block.get('hash')}")
                return False
        logger.info("All blocks integrity verification passed")
        return True
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories by query string (converts to keywords and semantic search)"""
        # Convert query to keywords
        keywords = [word.strip() for word in query.split() if word.strip()]
        return self.search_by_keywords(keywords, limit)
    
    def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """키워드로 블록 검색 (DatabaseManager 사용)"""
        return self.db_manager.search_blocks_by_keyword(keywords, limit=limit)
    
    def search_by_embedding(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """임베딩 유사도로 블록 검색"""
        return self.db_manager.search_blocks_by_embedding(query_embedding, top_k=top_k)
    
    def filter_by_importance(self, threshold: float = 0.7, limit: int = 100) -> List[Dict[str, Any]]:
        """중요도 기준으로 블록 필터링. DatabaseManager의 기능을 직접 호출."""
        # 현재 DatabaseManager에 해당 기능이 없으므로 get_blocks 후 필터링 (정렬 활용).
        # DB에서 직접 필터링 및 정렬하는 것이 훨씬 효율적임.
        # 예: self.db_manager.filter_blocks_by_importance(threshold, limit, sort_by='importance', order='desc')
        
        # 임시방편: 중요도로 정렬된 모든 블록을 가져온 후, Python에서 필터링 및 limit 적용
        # 이 방식은 DB에서 모든 데이터를 가져오므로 여전히 비효율적일 수 있음.
        # DB에 중요도 필터링 조건 + 정렬 + limit 기능을 구현해야 함.
        # all_important_blocks = self.db_manager.get_blocks(limit=limit*5, sort_by='importance', order='desc') # 더 많은 데이터를 가져와서 필터링
        # 
        # result = []
        # for block in all_important_blocks:
        #     if block.get('importance', 0.0) >= threshold:
        #         result.append(block)
        #     if len(result) >= limit:
        #         break
        # return result 
        return self.db_manager.filter_blocks_by_importance(threshold=threshold, limit=limit, order='desc')
    
    def verify_integrity(self) -> bool:
        """
        블록체인 무결성 검증
        
        Returns:
            bool: 블록체인이 무결성을 유지하면 True
        """
        try:
            # 1. 모든 블록 조회 (인덱스 순)
            blocks = self.db_manager.get_blocks()
            if not blocks:
                logger.info("No blocks to verify")
                return True
            
            # 2. 정렬 및 연속성 확인
            sorted_blocks = sorted(blocks, key=lambda x: x['block_index'])
            
            prev_hash = ""
            for i, block in enumerate(sorted_blocks):
                # 인덱스 연속성 확인
                expected_index = i
                if block['block_index'] != expected_index:
                    logger.error(f"Block index discontinuity: expected {expected_index}, got {block['block_index']}")
                    return False
                
                # 해시 체인 검증
                if block['prev_hash'] != prev_hash:
                    logger.error(f"Hash chain broken at block {i}: expected prev_hash '{prev_hash}', got '{block['prev_hash']}'")
                    return False
                
                # 현재 블록 해시 재계산 및 검증 (keywords, tags, embedding은 해시 계산에서 제외)
                calculated_hash = self._compute_hash({
                    'block_index': block['block_index'],
                    'timestamp': block['timestamp'],
                    'context': block['context'],
                    'importance': block['importance'],
                    'prev_hash': block['prev_hash']
                })
                
                if calculated_hash != block['hash']:
                    logger.error(f"Block {i} hash mismatch: calculated '{calculated_hash}', stored '{block['hash']}'")
                    return False
                
                prev_hash = block['hash']
            
            # 3. 메타데이터 일관성 확인 (블록 개수)
            total_blocks = len(sorted_blocks)
            last_block_index = sorted_blocks[-1]['block_index'] if sorted_blocks else -1
            
            logger.info(f"Blockchain integrity verified: {total_blocks} blocks")
            return True
        
        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            return False
    
    def update_block_links(self, block_index: int, neighbors: List[int]) -> bool:
        """
        Update neighbor links cache for a block (M2 Implementation).
        
        Args:
            block_index: Block index to update
            neighbors: List of neighbor block indices
            
        Returns:
            bool: True if update successful
        """
        try:
            # Get current block
            block = self.db_manager.get_block_by_index(block_index)
            if not block:
                logger.warning(f"Block {block_index} not found for links update")
                return False
            
            # Convert neighbor list to proper format
            neighbor_links = [{"id": idx, "weight": 1.0} for idx in neighbors if idx != block_index]
            
            # Update links in metadata
            metadata = block.get('metadata', {})
            if 'links' not in metadata:
                metadata['links'] = {}
            metadata['links']['neighbors'] = neighbor_links
            
            # Update block in database
            success = self.db_manager.update_block_metadata(block_index, metadata)
            if success:
                logger.debug(f"Updated links for block {block_index}: {len(neighbor_links)} neighbors")
                
                # GraphIndex 업데이트 (v3.0.0)
                if self.graph_index:
                    self._update_graph_index_links(block_index, neighbors)
                    
            else:
                logger.warning(f"Failed to update links for block {block_index}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error updating block links: {e}")
            return False
    
    def get_block_neighbors(self, block_index: int) -> List[int]:
        """
        Get cached neighbor links for a block.
        
        Args:
            block_index: Block index
            
        Returns:
            List of neighbor block indices or empty list if no cache
        """
        try:
            block = self.db_manager.get_block_by_index(block_index)
            if not block:
                return []
                
            metadata = block.get('metadata', {})
            links = metadata.get('links', {})
            neighbors = links.get('neighbors', [])
            
            # Extract block indices from neighbor data
            if neighbors and isinstance(neighbors[0], dict):
                return [n.get('id') for n in neighbors if isinstance(n.get('id'), int)]
            else:
                return neighbors  # Already a list of ints
            
        except Exception as e:
            logger.debug(f"Error getting block neighbors: {e}")
            return []
    
    # v2.5.1: AI Context Slots 통합 검색 기능
    def search_with_slots(self, query: str, limit: int = 5, use_slots: bool = True, 
                         include_relationships: bool = False, **options) -> List[Dict[str, Any]]:
        """
        v2.5.1 슬롯 시스템을 활용한 향상된 검색
        
        Args:
            query: 검색 쿼리
            limit: 반환할 결과 수
            use_slots: 슬롯 우선 검색 활성화
            include_relationships: 관계 기반 확장 검색 (v2.5.2+)
            **options: 추가 검색 옵션
                - slot: 특정 슬롯 지정 (예: 'A', 'B')
                - radius: 앵커 기반 검색 반경 (기본값: 2)
                - fallback: 국소 검색 실패 시 전역 검색 (기본값: True)
            
        Returns:
            검색 결과 리스트 (슬롯 + LTM 통합)
        """
        from datetime import datetime
        import time
        search_start_time = datetime.utcnow()
        metrics_start_time = time.time()
        
        # 메트릭 추적 변수
        search_type = None
        nodes_visited = 0
        edges_traversed = 0
        cache_hits = 0
        cache_misses = 0
        fallback_triggered = False
        
        # 옵션 파싱
        target_slot = options.get('slot', None)
        search_radius = options.get('radius', 2)
        use_fallback = options.get('fallback', True)
        
        logger.debug(f"Enhanced search: query='{query}', use_slots={use_slots}, slot={target_slot}, radius={search_radius}")
        
        all_results = []
        slots_results_count = 0
        ltm_results_count = 0
        graph_search_used = False
        fallback_used = False
        
        # Analytics 추적을 위한 변수
        analytics = None
        try:
            from .usage_analytics import UsageAnalytics
            analytics = UsageAnalytics()
        except ImportError:
            pass
        
        # 메트릭 업데이트
        self.metrics['total_searches'] += 1
        
        # Phase 0: 앵커 기반 국소 그래프 탐색 (NEW)
        if use_slots and target_slot:
            try:
                from .working_memory import AIContextualSlots
                slots = AIContextualSlots()
                slot = slots.get_slot(target_slot)
                
                if slot and slot.is_ltm_anchor() and slot.ltm_anchor_block:
                    # 앵커 주변 그래프 탐색
                    graph_results = self._search_local_graph(
                        anchor_block=slot.ltm_anchor_block,
                        radius=search_radius or slot.search_radius,
                        query=query,
                        limit=limit
                    )
                    
                    if graph_results:
                        for result in graph_results:
                            result['search_type'] = 'anchor_local'
                            result['slot_used'] = target_slot
                            result['radius_used'] = search_radius
                            result['graph_used'] = True  # 메트릭 추적용
                            # 홉 거리 메트릭 수집
                            if result.get('hop_distance') is not None:
                                self.metrics['total_hops'] += result['hop_distance']
                                self.metrics['search_count'] += 1
                        all_results.extend(graph_results)
                        graph_search_used = True
                        self.metrics['graph_searches'] += 1
                        self.metrics['graph_hits'] += len(graph_results)
                        logger.info(f"Graph search found {len(graph_results)} results from anchor {slot.ltm_anchor_block}")
                    
            except Exception as e:
                logger.error(f"Error in graph search: {e}")
        
        # Phase 1: 슬롯 우선 검색 (빠른 응답)
        if use_slots:
            try:
                from .working_memory import AIContextualSlots
                # 임시 슬롯 인스턴스 (실제로는 싱글톤이나 세션 기반으로 관리)
                slots = AIContextualSlots()
                active_slots = slots.get_all_active_slots()
                
                for slot_name, slot in active_slots.items():
                    if slot.matches_query(query):
                        # 슬롯 결과를 LTM 형식으로 변환
                        slot_result = {
                            'block_index': f"slot_{slot_name}",
                            'context': slot.content,
                            'timestamp': slot.timestamp.isoformat(),
                            'importance': slot.importance_score,
                            'source': 'working_memory',
                            'slot_type': slot.slot_type.value,
                            'keywords': self._extract_keywords_from_content(slot.content)
                        }
                        
                        # LTM 앵커인 경우 관련 블록 정보 추가
                        if slot.is_ltm_anchor():
                            slot_result['ltm_anchor_block'] = slot.ltm_anchor_block
                            slot_result['search_radius'] = slot.search_radius
                        
                        all_results.append(slot_result)
                        slots_results_count += 1
                        
                logger.debug(f"Found {slots_results_count} results from slots")
                        
            except ImportError:
                logger.warning("AIContextualSlots not available, skipping slot search")
            except Exception as e:
                logger.error(f"Error in slot search: {e}")
        
        # Phase 2: 기존 LTM 검색
        try:
            # 슬롯에서 찾은 만큼 제외하고 검색
            remaining_limit = max(1, limit - len(all_results))
            ltm_results = self.search_by_keywords(
                self._extract_keywords_from_content(query), 
                limit=remaining_limit
            )
            
            # 중복 제거 (슬롯 결과와 LTM 결과 간)
            unique_ltm_results = []
            for ltm_result in ltm_results:
                # 내용 유사성으로 중복 검사 (간단한 방식)
                is_duplicate = False
                for slot_result in all_results:
                    if self._is_content_similar(
                        ltm_result.get('context', ''), 
                        slot_result.get('context', '')
                    ):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    ltm_result['source'] = 'long_term_memory'
                    unique_ltm_results.append(ltm_result)
            
            all_results.extend(unique_ltm_results)
            ltm_results_count = len(unique_ltm_results)
            logger.debug(f"Added {ltm_results_count} unique LTM results")
            
        except Exception as e:
            logger.error(f"Error in LTM search: {e}")
        
        # Phase 2.5: Fallback 처리
        if not all_results and use_fallback and graph_search_used:
            # 그래프 검색이 실패했을 때만 fallback
            fallback_used = True
            logger.info("Graph search returned no results, falling back to global search")
        
        # Phase 3: 결과 랭킹 및 제한
        ranking_start_time = datetime.utcnow()
        ranked_results = self._rank_search_results(all_results, query)
        final_results = ranked_results[:limit]
        
        # 메타데이터 추가
        for result in final_results:
            if 'search_type' not in result:
                result['search_type'] = 'fallback' if fallback_used else 'standard'
            result['graph_used'] = graph_search_used
            result['fallback_used'] = fallback_used
        
        # 메트릭 수집
        try:
            from ..core.metrics_collector import MetricsCollector, SearchMetric, SearchType as MetricSearchType
            
            # 검색 타입 결정
            if target_slot and graph_search_used:
                metric_search_type = MetricSearchType.LOCAL_GRAPH
            elif use_slots:
                metric_search_type = MetricSearchType.SLOT_BASED
            elif fallback_triggered:
                metric_search_type = MetricSearchType.FALLBACK
            else:
                metric_search_type = MetricSearchType.GLOBAL
            
            # 메트릭 기록
            latency_ms = (time.time() - metrics_start_time) * 1000
            
            collector = MetricsCollector()
            metric = SearchMetric(
                timestamp=datetime.now(),
                search_type=metric_search_type,
                query=query[:100],  # 프라이버시를 위해 첫 100자만
                slot_used=target_slot,
                radius=search_radius if target_slot else None,
                total_results=len(final_results),
                relevant_results=len([r for r in final_results if r.get('score', 0) > 0.7]),
                latency_ms=latency_ms,
                hops_traversed=search_radius if graph_search_used else 0,
                top_score=final_results[0].get('score', 0) if final_results else 0,
                avg_score=sum(r.get('score', 0) for r in final_results) / len(final_results) if final_results else 0,
                fallback_triggered=fallback_triggered,
                nodes_visited=nodes_visited,
                edges_traversed=edges_traversed,
                cache_hits=cache_hits,
                cache_misses=cache_misses
            )
            collector.record_search(metric)
            logger.debug(f"Search metric recorded: type={metric_search_type.value}, latency={latency_ms:.1f}ms")
        except Exception as e:
            logger.debug(f"Failed to record search metric: {e}")
        
        # Analytics 추적: 검색 성능 비교
        if analytics:
            search_end_time = datetime.utcnow()
            total_search_time = (search_end_time - search_start_time).total_seconds() * 1000
            ranking_time = (search_end_time - ranking_start_time).total_seconds() * 1000
            
            # 기존 검색과 비교를 위해 기존 방식도 실행 (성능 측정용)
            baseline_start_time = datetime.utcnow()
            try:
                keywords = self._extract_keywords_from_content(query)
                baseline_results = self.search_by_keywords(keywords, limit=limit)
                baseline_end_time = datetime.utcnow()
                baseline_time = (baseline_end_time - baseline_start_time).total_seconds() * 1000
            except Exception:
                baseline_time = 0
                baseline_results = []
            
            # TODO: Implement track_search_comparison in UsageAnalytics
            # analytics.track_search_comparison(
            #     query_text=query[:100],  # 프라이버시를 위해 첫 100자만
            #     slots_enabled=use_slots,
            #     response_time_ms=total_search_time,
            #     results_count=len(final_results),
            #     slot_hits=slots_results_count,
            #     ltm_hits=ltm_results_count,
            #     top_result_source=final_results[0].get('source', 'unknown') if final_results else None
            # )
        
        logger.info(f"Enhanced search completed: {len(final_results)}/{len(all_results)} results returned")
        return final_results
    
    def _search_local_graph(self, anchor_block: int, radius: int, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        앵커 블록을 중심으로 한 국소 그래프 탐색
        
        Args:
            anchor_block: 시작 앵커 블록 인덱스
            radius: 탐색 반경 (hop 수)
            query: 검색 쿼리
            limit: 반환할 최대 결과 수
            
        Returns:
            그래프 탐색으로 찾은 블록 리스트
        """
        # GraphIndex를 사용할 수 있으면 beam_search 사용 (v3.0.0)
        if self.graph_index and hasattr(self.graph_index, 'beam_search'):
            try:
                # beam_search를 위한 목표 함수
                def is_goal(node_id: str) -> bool:
                    try:
                        block_idx = int(node_id)
                        block = self.db_manager.get_block_by_index(block_idx)
                        if block:
                            return self._matches_query(block, query)
                    except:
                        pass
                    return False
                
                # GraphIndex beam_search 사용
                hit_nodes = self.graph_index.beam_search(
                    start=str(anchor_block),
                    is_goal=is_goal,
                    beam=32,
                    max_hop=radius
                )
                
                # 결과 변환
                results = []
                for i, node_id in enumerate(hit_nodes[:limit]):
                    block_idx = int(node_id)
                    block = self.db_manager.get_block_by_index(block_idx)
                    if block:
                        block_dict = block.to_dict() if hasattr(block, 'to_dict') else block
                        block_dict['hop_distance'] = i  # 실제 거리는 beam_search가 추적해야 함
                        block_dict['anchor_block'] = anchor_block
                        results.append(block_dict)
                
                return results
                
            except Exception as e:
                logger.debug(f"GraphIndex search failed, falling back to BFS: {e}")
        
        # Fallback: 기존 BFS 사용
        results = []
        visited = set()
        queue = [(anchor_block, 0)]  # (block_id, distance)
        
        while queue and len(results) < limit:
            current_block, distance = queue.pop(0)
            
            if current_block in visited or distance > radius:
                continue
                
            visited.add(current_block)
            
            # 현재 블록 가져오기
            block = self.db_manager.get_block_by_index(current_block)
            if block and self._matches_query(block, query):
                block_dict = block.to_dict() if hasattr(block, 'to_dict') else block
                block_dict['hop_distance'] = distance
                block_dict['anchor_block'] = anchor_block
                results.append(block_dict)
            
            # 이웃 블록들 탐색 (거리가 radius 이내인 경우만)
            if distance < radius:
                neighbors = self.get_block_neighbors(current_block)
                for neighbor_id in neighbors:
                    if neighbor_id not in visited:
                        queue.append((neighbor_id, distance + 1))
        
        # 거리 기반 정렬 (가까운 것부터)
        results.sort(key=lambda x: x.get('hop_distance', float('inf')))
        
        return results[:limit]
    
    def _matches_query(self, block: Any, query: str) -> bool:
        """블록이 쿼리와 매치되는지 확인"""
        if not block:
            return False
            
        # 간단한 키워드 매칭 (향후 임베딩 기반으로 개선 가능)
        query_lower = query.lower()
        block_content = str(block.get('context', '') if isinstance(block, dict) else getattr(block, 'context', ''))
        block_keywords = block.get('keywords', []) if isinstance(block, dict) else getattr(block, 'keywords', [])
        
        # 컨텐츠나 키워드에 쿼리가 포함되어 있는지 확인
        if query_lower in block_content.lower():
            return True
            
        for keyword in block_keywords:
            if query_lower in str(keyword).lower():
                return True
                
        return False
    
    def _update_near_anchor_links(self, new_block_index: int, metadata: Dict[str, Any]) -> int:
        """
        Near-Anchor Write: 새 블록을 활성 앵커 주변 네트워크에 연결
        
        Args:
            new_block_index: 새로 추가된 블록의 인덱스
            metadata: 블록의 메타데이터
            
        Returns:
            생성된 링크 수
        """
        links_created = 0
        try:
            from .working_memory import AIContextualSlots
            slots = AIContextualSlots()
            
            # 모든 활성 앵커 찾기
            active_anchors = []
            for slot_name in ['A', 'B', 'C', 'D', 'E']:
                slot = slots.get_slot(slot_name)
                if slot and slot.is_ltm_anchor() and slot.ltm_anchor_block:
                    active_anchors.append(slot.ltm_anchor_block)
            
            if not active_anchors:
                return 0
            
            # 가장 가까운 앵커 찾기 (임베딩 기반으로 개선 가능)
            nearest_anchor = active_anchors[0]  # 일단 첫 번째 앵커 사용
            
            # 양방향 링크 생성
            self.update_block_links(new_block_index, [nearest_anchor])
            self.update_block_links(nearest_anchor, [new_block_index])
            links_created += 2  # 양방향 링크
            
            # 앵커의 이웃들과도 연결 (2-hop 네트워크)
            anchor_neighbors = self.get_block_neighbors(nearest_anchor)
            if anchor_neighbors:
                # 상위 3개 이웃과 연결
                top_neighbors = anchor_neighbors[:3]
                self.update_block_links(new_block_index, top_neighbors)
                links_created += len(top_neighbors)
                
            logger.info(f"Connected new block {new_block_index} to anchor {nearest_anchor} network with {links_created} links")
            
        except Exception as e:
            logger.debug(f"Near-anchor write not available: {e}")
        
        return links_created
    
    def _extract_keywords_from_content(self, content: str, max_keywords: int = 5) -> List[str]:
        """컨텐츠에서 간단한 키워드 추출"""
        try:
            from ..text_utils import extract_keywords_from_text
            return extract_keywords_from_text(content)[:max_keywords]
        except ImportError:
            # 간단한 폴백: 공백으로 분할
            words = content.split()
            return [word.strip('.,!?') for word in words if len(word) > 2][:max_keywords]
    
    def _is_content_similar(self, content1: str, content2: str, threshold: float = 0.7) -> bool:
        """두 컨텐츠의 유사성 검사 (간단한 방식)"""
        if not content1 or not content2:
            return False
            
        # 간단한 자카드 유사도
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return False
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    def _rank_search_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """검색 결과 랭킹 (슬롯 우선, 중요도, 최신성 고려)"""
        def calculate_score(result):
            score = 0.0
            
            # 슬롯 결과 우선순위 (빠른 응답)
            if result.get('source') == 'working_memory':
                score += 10.0
                
                # 슬롯 타입별 가중치
                slot_type = result.get('slot_type', 'context')
                if slot_type == 'anchor':
                    score += 5.0  # 앵커 슬롯 높은 우선순위
                elif slot_type == 'context':
                    score += 3.0  # 활성 컨텍스트
                else:  # buffer
                    score += 1.0
            
            # 중요도 점수
            importance = result.get('importance', 0.5)
            score += importance * 5.0
            
            # 최신성 점수 (간단화)
            try:
                timestamp_str = result.get('timestamp', '')
                if timestamp_str:
                    # 최근일수록 높은 점수 (세부 구현은 생략)
                    score += 1.0
            except:
                pass
            
            return score
        
        return sorted(results, key=calculate_score, reverse=True)
    
    # v2.7.0: Causal Reasoning Methods
    
    def get_causal_relationships(self, block_id: int) -> List[Dict[str, Any]]:
        """
        특정 블록의 인과관계 조회
        
        Args:
            block_id: 조회할 블록 ID
            
        Returns:
            인과관계 리스트
        """
        if not self.causal_manager:
            logger.warning("Causal reasoning not available")
            return []
        
        return self.causal_manager.get_relationships_for_block(block_id)
    
    def get_causal_statistics(self) -> Dict[str, Any]:
        """
        인과관계 감지 통계 조회
        
        Returns:
            통계 정보 딕셔너리
        """
        if not self.causal_manager:
            return {'error': 'Causal reasoning not available'}
        
        return self.causal_manager.get_detection_statistics()
    
    def find_causal_chain(self, start_block_id: int, max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        인과관계 체인 탐색 (A → B → C → D 형태)
        
        Args:
            start_block_id: 시작 블록 ID
            max_depth: 최대 탐색 깊이
            
        Returns:
            인과관계 체인 리스트
        """
        if not self.causal_manager:
            return []
        
        try:
            conn = self.db_manager._get_connection()
            cursor = conn.cursor()
            
            # 재귀적으로 인과관계 체인 탐색
            chain = []
            visited = set()
            
            def traverse_chain(current_id: int, depth: int):
                if depth >= max_depth or current_id in visited:
                    return
                
                visited.add(current_id)
                
                # 현재 블록이 원인이 되는 관계들 찾기
                cursor.execute('''
                    SELECT target_block_id, relation_type, confidence
                    FROM causal_relationships 
                    WHERE source_block_id = ? AND confidence >= 0.5
                    ORDER BY confidence DESC
                ''', (current_id,))
                
                for row in cursor.fetchall():
                    target_id, relation_type, confidence = row
                    
                    # 블록 정보 조회
                    target_block = self.db_manager.get_block(target_id)
                    if target_block:
                        chain.append({
                            'source_id': current_id,
                            'target_id': target_id,
                            'relation_type': relation_type,
                            'confidence': confidence,
                            'target_block': target_block,
                            'depth': depth
                        })
                        
                        # 재귀적으로 계속 탐색
                        traverse_chain(target_id, depth + 1)
            
            traverse_chain(start_block_id, 0)
            return chain
            
        except Exception as e:
            logger.error(f"Failed to find causal chain from block {start_block_id}: {e}")
            return []
    
    def get_metrics(self) -> Dict[str, Any]:
        """검색 및 성능 메트릭 반환"""
        # 평균 계산
        if self.metrics['graph_searches'] > 0:
            self.metrics['local_hit_rate'] = self.metrics['graph_hits'] / self.metrics['graph_searches']
        else:
            self.metrics['local_hit_rate'] = 0.0
            
        if self.metrics['search_count'] > 0:
            self.metrics['avg_hops'] = self.metrics['total_hops'] / self.metrics['search_count']
        else:
            self.metrics['avg_hops'] = 0.0
            
        return {
            'total_searches': self.metrics['total_searches'],
            'graph_searches': self.metrics['graph_searches'],
            'graph_hits': self.metrics['graph_hits'],
            'local_hit_rate': round(self.metrics['local_hit_rate'], 3),
            'avg_hops': round(self.metrics['avg_hops'], 2),
            'fallback_searches': self.metrics['fallback_searches']
        }
        
    def reset_metrics(self):
        """메트릭 초기화"""
        self.metrics = {
            'total_searches': 0,
            'graph_searches': 0,
            'graph_hits': 0,
            'fallback_searches': 0,
            'total_hops': 0,
            'search_count': 0,
            'avg_response_time': 0.0,
            'local_hit_rate': 0.0,
            'avg_hops': 0.0
        }
    
    # GraphIndex 관련 메서드들 (v3.0.0)
    
    def _auto_bootstrap_graph_index(self):
        """첫 실행 시 자동 부트스트랩"""
        if not self.graph_index:
            return
        
        try:
            # 기존 블록이 있는지 확인
            blocks = self.get_blocks(limit=1)
            if blocks and len(self.graph_index.adj) == 0:
                # GraphIndex가 비어있으면 부트스트랩
                self.bootstrap_graph_index()
        except Exception as e:
            logger.debug(f"Auto-bootstrap skipped: {e}")
    
    def bootstrap_graph_index(self):
        """기존 블록들로부터 GraphIndex를 부트스트랩"""
        if not self.graph_index:
            logger.warning("GraphIndex not available")
            return
        
        logger.info("Bootstrapping GraphIndex from existing blocks...")
        
        # 모든 블록 가져오기
        blocks = self.get_blocks(limit=10000)  # 실제로는 페이징 필요
        
        for block in blocks:
            block_idx = block.get('block_index')
            if block_idx is None:
                continue
            
            node_id = str(block_idx)
            
            # 노드 추가
            if node_id not in self.graph_index.adj:
                self.graph_index.adj[node_id] = []
            
            # 메타데이터에서 링크 정보 추출
            metadata = block.get('metadata', {})
            links = metadata.get('links', {})
            neighbors = links.get('neighbors', [])
            
            for neighbor in neighbors:
                if isinstance(neighbor, dict):
                    neighbor_id = str(neighbor.get('id'))
                    weight = neighbor.get('weight', 1.0)
                else:
                    neighbor_id = str(neighbor)
                    weight = 1.0
                
                # 엣지 추가 (중복 체크)
                existing = {n[0] for n in self.graph_index.adj[node_id]}
                if neighbor_id not in existing:
                    self.graph_index.adj[node_id].append((neighbor_id, weight))
        
        # 모든 노드의 이웃 정렬 및 제한
        for node_id in self.graph_index.adj:
            self.graph_index.adj[node_id].sort(key=lambda x: x[1], reverse=True)
            self.graph_index.adj[node_id] = self.graph_index.adj[node_id][:self.graph_index.kmax]
        
        logger.info(f"GraphIndex bootstrapped with {len(self.graph_index.adj)} nodes")
    
    def bootstrap_and_save_graph(self, output_path):
        """GraphIndex를 부트스트랩하고 스냅샷 저장"""
        if not self.graph_index:
            logger.error("GraphIndex not available")
            return None
        
        self.bootstrap_graph_index()
        
        # 스냅샷 저장
        try:
            from ..graph.snapshot import save_graph_snapshot
            
            # 파라미터 준비
            params = {
                "theta": self.graph_index.theta,
                "kmax": self.graph_index.kmax,
                "alpha": 0.7,
                "beta": 0.2,
                "gamma": 0.1
            }
            
            save_graph_snapshot(self.graph_index.adj, params, output_path)
            return output_path
        except ImportError as e:
            logger.error(f"Graph snapshot not available: {e}")
            return None
    
    def _update_graph_index_links(self, block_index: int, neighbors: List[int]):
        """GraphIndex의 링크 정보를 업데이트"""
        if not self.graph_index:
            return
        
        try:
            node_id = str(block_index)
            
            # 노드가 없으면 추가
            if node_id not in self.graph_index.adj:
                self.graph_index.adj[node_id] = []
            
            # 기존 이웃들 가져오기
            existing_neighbors = {n[0] for n in self.graph_index.adj[node_id]}
            
            # 새 이웃들 추가
            for neighbor_idx in neighbors:
                neighbor_id = str(neighbor_idx)
                if neighbor_id not in existing_neighbors:
                    # 가중치 1.0으로 추가
                    self.graph_index.adj[node_id].append((neighbor_id, 1.0))
                    
                    # 양방향 엣지 (이웃에도 추가)
                    if neighbor_id not in self.graph_index.adj:
                        self.graph_index.adj[neighbor_id] = []
                    
                    neighbor_existing = {n[0] for n in self.graph_index.adj[neighbor_id]}
                    if node_id not in neighbor_existing:
                        self.graph_index.adj[neighbor_id].append((node_id, 1.0))
            
            # 가중치 기준 정렬 및 제한
            self.graph_index.adj[node_id].sort(key=lambda x: x[1], reverse=True)
            self.graph_index.adj[node_id] = self.graph_index.adj[node_id][:self.graph_index.kmax]
            
        except Exception as e:
            logger.debug(f"Failed to update GraphIndex links: {e}")