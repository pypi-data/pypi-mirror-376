"""
Greeum v3.0.0: Migration Bridge
Allows gradual transition from v2.6.4 to v3.0 with full compatibility
"""

import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.core.context_memory import ContextMemorySystem

logger = logging.getLogger(__name__)


class V3MigrationBridge:
    """
    Hybrid system that supports both v2.6.4 and v3.0 operations
    Allows gradual migration without breaking existing functionality
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize migration bridge with both systems"""
        
        # Shared database
        self.db_manager = DatabaseManager(connection_string=db_path)
        
        # v2.6.4 system (legacy)
        self.legacy_blocks = BlockManager(self.db_manager)
        
        # v3.0 system (new)
        self.context_memory = ContextMemorySystem(db_path)
        
        # Migration tracking
        self.migrated_blocks = set()
        self.mode = 'hybrid'  # 'legacy', 'v3', 'hybrid'
        
        logger.info(f"Migration Bridge initialized in {self.mode} mode")
    
    def add_memory(self, content: str, importance: float = 0.5, 
                   keywords: Optional[List[str]] = None,
                   tags: Optional[List[str]] = None) -> int:
        """
        Add memory to both systems for seamless transition
        
        Args:
            content: Memory content
            importance: Importance score
            keywords: Optional keywords (for v2.6.4 compatibility)
            tags: Optional tags (for v2.6.4 compatibility)
            
        Returns:
            Memory/block index
        """
        result_id = None
        
        # v2.6.4 legacy storage
        if self.mode in ['legacy', 'hybrid']:
            # Use provided keywords/tags or extract them
            if not keywords:
                keywords = self._extract_keywords(content)
            if not tags:
                tags = []
            
            legacy_result = self.legacy_blocks.add_block(
                context=content,
                keywords=keywords,
                tags=tags,
                embedding=[],  # Will be computed
                importance=importance,
                metadata={'v3_compatible': True}
            )
            
            if legacy_result:
                result_id = legacy_result['block_index']
                logger.debug(f"Added to v2.6.4: block #{result_id}")
        
        # v3.0 context-aware storage
        if self.mode in ['v3', 'hybrid']:
            v3_id = self.context_memory.add_memory(content, importance)
            
            if self.mode == 'v3':
                result_id = v3_id
            
            logger.debug(f"Added to v3.0: memory #{v3_id}")
            
            # Create lazy connections for unmigrated blocks
            if self.mode == 'hybrid':
                self._create_lazy_connections(v3_id, content)
        
        return result_id if result_id is not None else -1
    
    def search(self, query: str, limit: int = 5, 
               use_v3_activation: bool = True) -> List[Dict]:
        """
        Search across both systems with unified results
        
        Args:
            query: Search query
            limit: Max results
            use_v3_activation: Use v3.0 spreading activation
            
        Returns:
            Unified search results
        """
        all_results = []
        
        # v2.6.4 search
        if self.mode in ['legacy', 'hybrid']:
            # Search using keywords
            keywords = self._extract_keywords(query)
            legacy_results = []
            
            # Get all blocks and filter
            last_block_info = self.db_manager.get_last_block_info()
            if last_block_info:
                for i in range(min(last_block_info[0] + 1, limit * 2)):
                    block = self.db_manager.get_block(i)
                    if block:
                        # Check if query matches content
                        if any(keyword in block.get('context', '').lower() 
                               for keyword in keywords):
                            block['source'] = 'v2.6.4'
                            legacy_results.append(block)
                            if len(legacy_results) >= limit:
                                break
            
            all_results.extend(legacy_results)
            
            logger.debug(f"Found {len(legacy_results)} in v2.6.4")
        
        # v3.0 context-aware search
        if self.mode in ['v3', 'hybrid']:
            v3_results = self.context_memory.recall(query, use_activation=use_v3_activation)
            for result in v3_results[:limit]:
                result['source'] = 'v3.0'
                all_results.append(result)
            
            logger.debug(f"Found {len(v3_results)} in v3.0")
        
        # Deduplicate and rank
        return self._merge_and_rank(all_results, limit)
    
    def migrate_block(self, block_index: int) -> bool:
        """
        Migrate a specific v2.6.4 block to v3.0 with context inference
        
        Args:
            block_index: Block to migrate
            
        Returns:
            Success status
        """
        if block_index in self.migrated_blocks:
            logger.info(f"Block #{block_index} already migrated")
            return True
        
        # Get v2.6.4 block
        block = self.db_manager.get_block(block_index)
        if not block:
            logger.error(f"Block #{block_index} not found")
            return False
        
        # Infer context from temporal proximity
        timestamp = block.get('timestamp', time.time())
        context_trigger = self._infer_context(block_index, timestamp)
        
        # Switch to inferred context
        self.context_memory.switch_context(context_trigger)
        
        # Add to v3.0 system
        v3_id = self.context_memory.add_memory(
            block['context'],
            block.get('importance', 0.5)
        )
        
        # Create connections based on temporal/semantic similarity
        self._migrate_connections(block_index, v3_id)
        
        self.migrated_blocks.add(block_index)
        logger.info(f"Migrated block #{block_index} to v3.0 memory #{v3_id}")
        
        return True
    
    def batch_migrate(self, start_index: int = 0, 
                      end_index: Optional[int] = None,
                      batch_size: int = 10) -> Dict[str, Any]:
        """
        Migrate multiple blocks in batches
        
        Args:
            start_index: Starting block index
            end_index: Ending block index (None for all)
            batch_size: Blocks per batch
            
        Returns:
            Migration statistics
        """
        stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'already_migrated': 0
        }
        
        # Get range
        if end_index is None:
            last_block = self.db_manager.get_last_block_info()
            end_index = last_block[0] if last_block else start_index
        
        # Process in batches
        for batch_start in range(start_index, end_index + 1, batch_size):
            batch_end = min(batch_start + batch_size, end_index + 1)
            
            logger.info(f"Migrating batch: {batch_start} to {batch_end - 1}")
            
            for block_index in range(batch_start, batch_end):
                stats['total'] += 1
                
                if block_index in self.migrated_blocks:
                    stats['already_migrated'] += 1
                    continue
                
                if self.migrate_block(block_index):
                    stats['successful'] += 1
                else:
                    stats['failed'] += 1
            
            # Small delay between batches
            time.sleep(0.1)
        
        logger.info(f"Migration complete: {stats}")
        return stats
    
    def _create_lazy_connections(self, memory_id: int, content: str):
        """Create connections to existing blocks on first access"""
        # Find temporally close blocks
        recent_blocks = []
        last_block_info = self.db_manager.get_last_block_info()
        if last_block_info:
            start = max(0, last_block_info[0] - 10)
            for i in range(start, last_block_info[0] + 1):
                block = self.db_manager.get_block(i)
                if block:
                    recent_blocks.append(block)
        
        for block in recent_blocks:
            if block['block_index'] != memory_id:
                # Simple similarity check (in production, use embeddings)
                similarity = self._compute_similarity(content, block['context'])
                if similarity > 0.3:
                    # Would create connection in v3 system
                    logger.debug(f"Lazy connection: {memory_id} <-> {block['block_index']}")
    
    def _infer_context(self, block_index: int, timestamp: float) -> str:
        """Infer context from temporal patterns"""
        # Get nearby blocks
        nearby = []
        for i in range(max(0, block_index - 5), block_index + 5):
            block = self.db_manager.get_block(i)
            if block:
                nearby.append(block)
        
        # Simple heuristic: group by time gaps
        if nearby:
            time_gaps = []
            for i in range(1, len(nearby)):
                gap = abs(nearby[i].get('timestamp', 0) - nearby[i-1].get('timestamp', 0))
                time_gaps.append(gap)
            
            avg_gap = sum(time_gaps) / len(time_gaps) if time_gaps else 3600
            
            # Large gap suggests context switch
            if any(gap > avg_gap * 3 for gap in time_gaps):
                return f"context_boundary_{block_index}"
        
        return f"inferred_context_{int(timestamp // 3600)}"
    
    def _migrate_connections(self, old_id: int, new_id: int):
        """Migrate connections from v2.6.4 to v3.0"""
        # In v2.6.4, connections are implicit (temporal/semantic)
        # In v3.0, we make them explicit
        
        # Find related blocks
        block = self.db_manager.get_block(old_id)
        if not block:
            return
        
        # Search for semantically similar blocks
        keywords = block.get('keywords', [])
        for keyword in keywords[:3]:  # Top 3 keywords
            related = self.db_manager.search_blocks(keyword, limit=5)
            for rel_block in related:
                if rel_block['block_index'] != old_id:
                    # Would create connection in v3.0
                    logger.debug(f"Migrated connection: {new_id} <-> {rel_block['block_index']}")
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity (use embeddings in production)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _merge_and_rank(self, results: List[Dict], limit: int) -> List[Dict]:
        """Merge and deduplicate results from both systems"""
        seen_content = set()
        unique_results = []
        
        for result in results:
            content = result.get('context', '')
            content_key = content[:50]  # First 50 chars as key
            
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_results.append(result)
        
        # Sort by relevance (activation score if available, else importance)
        unique_results.sort(
            key=lambda x: x.get('activation_score', x.get('importance', 0)),
            reverse=True
        )
        
        return unique_results[:limit]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        import re
        words = re.findall(r'\b[a-zA-Z가-힣]+\b', text.lower())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     '은', '는', '이', '가', '을', '를', '에', '의'}
        return [w for w in words if len(w) > 2 and w not in stop_words][:5]
    
    def set_mode(self, mode: str):
        """
        Set operation mode
        
        Args:
            mode: 'legacy', 'v3', or 'hybrid'
        """
        if mode in ['legacy', 'v3', 'hybrid']:
            self.mode = mode
            logger.info(f"Switched to {mode} mode")
        else:
            logger.error(f"Invalid mode: {mode}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        stats = {
            'mode': self.mode,
            'migrated_blocks': len(self.migrated_blocks),
            'v3_contexts': len(self.context_memory.context_manager.contexts)
            if hasattr(self.context_memory.context_manager, 'contexts') else 0,
            'active_context': self.context_memory.get_context_info()
        }
        
        # v2.6.4 stats
        last_block = self.db_manager.get_last_block_info()
        if last_block:
            stats['v2_total_blocks'] = last_block[0] + 1
        
        return stats