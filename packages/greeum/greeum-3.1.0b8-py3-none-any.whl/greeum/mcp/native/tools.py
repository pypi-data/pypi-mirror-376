#!/usr/bin/env python3
"""
Greeum Native MCP Server - MCP Tools Implementation
BaseAdapter를 통해 v3 기능 완전 지원

핵심 기능:
- BaseAdapter의 v3 슬롯/브랜치 시스템 활용
- 스마트 라우팅 및 메타데이터 지원
- DFS 우선 검색
- MCP 프로토콜 응답 형식 준수
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import hashlib

# BaseAdapter import
from ..adapters.base_adapter import BaseAdapter

logger = logging.getLogger("greeum_native_tools")

class GreeumMCPTools(BaseAdapter):
    """
    Greeum MCP 도구 핸들러

    BaseAdapter를 상속받아 v3 기능 완전 지원:
    - 슬롯/브랜치 시스템
    - 스마트 라우팅
    - DFS 우선 검색
    - 모든 최신 기능 포함
    """

    def __init__(self, greeum_components: Dict[str, Any]):
        """
        Args:
            greeum_components: DatabaseManager, BlockManager 등이 포함된 딕셔너리
        """
        # BaseAdapter 초기화
        super().__init__()
        # 컴포넌트 직접 설정 (이미 초기화된 것 사용)
        self.components = greeum_components
        self.initialized = True
        logger.info("Greeum MCP tools initialized with BaseAdapter v3 features")

    def _get_version(self) -> str:
        """중앙화된 버전 참조"""
        try:
            from greeum import __version__
            return __version__
        except ImportError:
            return "unknown"

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        도구 실행 메인 라우터

        Args:
            tool_name: 실행할 도구 이름 (add_memory, search_memory 등)
            arguments: 도구에 전달할 파라미터

        Returns:
            str: MCP 형식의 응답 텍스트
        """
        try:
            if tool_name == "add_memory":
                return await self._handle_add_memory(arguments)
            elif tool_name == "search_memory":
                return await self._handle_search_memory(arguments)
            elif tool_name == "get_memory_stats":
                return await self._handle_get_memory_stats(arguments)
            elif tool_name == "usage_analytics":
                return await self._handle_usage_analytics(arguments)
            elif tool_name == "analyze_causality":
                return await self._handle_analyze_causality(arguments)
            elif tool_name == "infer_causality":
                return await self._handle_infer_causality(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            raise ValueError(f"Tool execution failed: {e}")

    async def _handle_add_memory(self, arguments: Dict[str, Any]) -> str:
        """
        add_memory 도구 처리 - BaseAdapter의 v3 기능 사용

        v3 기능 포함:
        1. 중복 검사
        2. 품질 검증
        3. 슬롯/브랜치 기반 메모리 추가
        4. 스마트 라우팅
        5. 사용 통계 로깅
        """
        try:
            # 파라미터 추출
            content = arguments.get("content")
            if not content:
                raise ValueError("content parameter is required")

            importance = arguments.get("importance", 0.5)
            if not (0.0 <= importance <= 1.0):
                raise ValueError("importance must be between 0.0 and 1.0")

            # BaseAdapter의 add_memory_tool 직접 사용 (v3 기능 모두 포함)
            result = self.add_memory_tool(content, importance)
            return result

        except Exception as e:
            logger.error(f"add_memory failed: {e}")
            return f"ERROR: Failed to add memory: {str(e)}"

    async def _handle_search_memory(self, arguments: Dict[str, Any]) -> str:
        """
        search_memory 도구 처리 - BaseAdapter의 v3 검색 사용

        v3 기능:
        1. DFS 우선 검색
        2. 슬롯 기반 검색
        3. 연관관계 확장 탐색
        4. 사용 통계 로깅
        """
        try:
            # 파라미터 추출
            query = arguments.get("query")
            if not query:
                raise ValueError("query parameter is required")

            limit = arguments.get("limit", 5)
            if not (1 <= limit <= 200):
                raise ValueError("limit must be between 1 and 200")

            # v3 파라미터들
            depth = arguments.get("depth", 0)  # 연관 탐색 심도
            if not (0 <= depth <= 3):
                raise ValueError("depth must be between 0 and 3")

            tolerance = arguments.get("tolerance", 0.5)  # 검색 허용 오차
            if not (0.0 <= tolerance <= 1.0):
                raise ValueError("tolerance must be between 0.0 and 1.0")

            entry = arguments.get("entry", "cursor")  # v3 진입점 타입
            if entry not in ["cursor", "head"]:
                entry = "cursor"

            # BaseAdapter의 search_memory_tool 사용 (v3 기능 포함)
            result = self.search_memory_tool(query, limit, depth, tolerance, entry)
            return result

        except Exception as e:
            logger.error(f"search_memory failed: {e}")
            return f"ERROR: Search failed: {str(e)}"

    async def _handle_get_memory_stats(self, arguments: Dict[str, Any]) -> str:
        """
        get_memory_stats 도구 처리 - BaseAdapter 사용
        """
        try:
            # BaseAdapter의 get_memory_stats_tool 사용
            result = self.get_memory_stats_tool()
            return result

        except Exception as e:
            logger.error(f"get_memory_stats failed: {e}")
            return f"ERROR: Failed to get memory stats: {str(e)}"

    async def _handle_usage_analytics(self, arguments: Dict[str, Any]) -> str:
        """
        usage_analytics 도구 처리 - BaseAdapter 사용
        """
        try:
            # 파라미터 추출
            days = arguments.get("days", 7)
            if not (1 <= days <= 90):
                raise ValueError("days must be between 1 and 90")

            report_type = arguments.get("report_type", "usage")
            if report_type not in ["usage", "quality", "performance", "all"]:
                report_type = "usage"

            # BaseAdapter의 usage_analytics_tool 사용
            result = self.usage_analytics_tool(days, report_type)
            return result

        except Exception as e:
            logger.error(f"usage_analytics failed: {e}")
            return f"ERROR: Failed to get usage analytics: {str(e)}"

    async def _handle_analyze_causality(self, arguments: Dict[str, Any]) -> str:
        """
        analyze_causality 도구 처리

        인과관계 분석 (추후 BaseAdapter로 이전 예정)
        """
        try:
            # 파라미터 추출
            memory_ids = arguments.get("memory_ids")
            if not memory_ids or not isinstance(memory_ids, list):
                raise ValueError("memory_ids parameter is required and must be a list")

            # 컴포넌트 확인
            if not self._check_components():
                return "ERROR: Greeum components not available"

            # CausalEngine이 있는지 확인
            causal_engine = self.components.get('causal_engine')
            if not causal_engine:
                return "ERROR: Causal analysis not available in current configuration"

            # 인과관계 분석 수행
            results = []
            for i in range(len(memory_ids) - 1):
                cause_id = memory_ids[i]
                effect_id = memory_ids[i + 1]

                # 메모리 블록 가져오기
                cause_block = self.components['db_manager'].get_block(cause_id)
                effect_block = self.components['db_manager'].get_block(effect_id)

                if cause_block and effect_block:
                    # 인과관계 분석
                    relationship = causal_engine.analyze_causality(
                        cause_block['context'],
                        effect_block['context']
                    )

                    results.append({
                        "cause": cause_id,
                        "effect": effect_id,
                        "confidence": relationship.get('confidence', 0.0),
                        "type": relationship.get('type', 'unknown')
                    })

            # 결과 포맷팅
            if results:
                output = "CAUSALITY ANALYSIS RESULTS:\n\n"
                for r in results:
                    output += f"• Block #{r['cause']} → Block #{r['effect']}\n"
                    output += f"  Confidence: {r['confidence']:.1%}\n"
                    output += f"  Type: {r['type']}\n\n"
                return output
            else:
                return "No valid memory blocks found for analysis"

        except Exception as e:
            logger.error(f"analyze_causality failed: {e}")
            return f"ERROR: Causality analysis failed: {str(e)}"

    async def _handle_infer_causality(self, arguments: Dict[str, Any]) -> str:
        """
        infer_causality 도구 처리

        인과관계 추론 (추후 BaseAdapter로 이전 예정)
        """
        try:
            # 파라미터 추출
            query = arguments.get("query")
            if not query:
                raise ValueError("query parameter is required")

            limit = arguments.get("limit", 5)
            if not (1 <= limit <= 20):
                raise ValueError("limit must be between 1 and 20")

            # 컴포넌트 확인
            if not self._check_components():
                return "ERROR: Greeum components not available"

            # CausalEngine이 있는지 확인
            causal_engine = self.components.get('causal_engine')
            if not causal_engine:
                return "ERROR: Causal inference not available in current configuration"

            # 인과관계 추론 수행
            inferences = causal_engine.infer_from_query(query, limit)

            # 결과 포맷팅
            if inferences:
                output = f"CAUSAL INFERENCES FOR: '{query}'\n\n"
                for i, inf in enumerate(inferences, 1):
                    output += f"{i}. {inf['description']}\n"
                    output += f"   Confidence: {inf['confidence']:.1%}\n"
                    if inf.get('supporting_memories'):
                        output += f"   Based on: {', '.join(f'#{m}' for m in inf['supporting_memories'])}\n"
                    output += "\n"
                return output
            else:
                return f"No causal inferences found for query: '{query}'"

        except Exception as e:
            logger.error(f"infer_causality failed: {e}")
            return f"ERROR: Causal inference failed: {str(e)}"

    def _check_components(self) -> bool:
        """
        컴포넌트 가용성 확인
        """
        required = ['db_manager', 'duplicate_detector', 'quality_validator', 'usage_analytics']
        for comp in required:
            if comp not in self.components or self.components[comp] is None:
                logger.error(f"Required component missing: {comp}")
                return False
        return True