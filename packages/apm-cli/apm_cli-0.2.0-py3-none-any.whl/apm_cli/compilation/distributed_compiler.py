"""Distributed AGENTS.md compilation system following the Minimal Context Principle.

This module implements hierarchical directory-based distribution to generate multiple 
AGENTS.md files across a project's directory structure, following the AGENTS.md standard 
for nested agent context files.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

from ..primitives.models import Instruction, PrimitiveCollection
from ..version import get_version
from .template_builder import TemplateData, find_chatmode_by_name
from .constants import BUILD_ID_PLACEHOLDER


@dataclass
class DirectoryMap:
    """Mapping of directory structure analysis."""
    directories: Dict[Path, Set[str]]  # directory -> set of applicable file patterns
    depth_map: Dict[Path, int]  # directory -> depth level
    parent_map: Dict[Path, Optional[Path]]  # directory -> parent directory
    
    def get_max_depth(self) -> int:
        """Get maximum depth in the directory structure."""
        return max(self.depth_map.values()) if self.depth_map else 0


@dataclass 
class PlacementResult:
    """Result of AGENTS.md placement analysis."""
    agents_path: Path
    instructions: List[Instruction]
    inherited_instructions: List[Instruction] = field(default_factory=list)
    coverage_patterns: Set[str] = field(default_factory=set)
    source_attribution: Dict[str, str] = field(default_factory=dict)  # instruction_id -> source


@dataclass
class CompilationResult:
    """Result of distributed AGENTS.md compilation."""
    success: bool
    placements: List[PlacementResult]
    content_map: Dict[Path, str]  # agents_path -> content
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)


class DistributedAgentsCompiler:
    """Main compiler for generating distributed AGENTS.md files."""
    
    def __init__(self, base_dir: str = "."):
        """Initialize the distributed compiler.
        
        Args:
            base_dir (str): Base directory for compilation. Defaults to current directory.
        """
        try:
            self.base_dir = Path(base_dir).resolve()
        except (OSError, FileNotFoundError):
            # Handle invalid path contexts (e.g., test environments)
            self.base_dir = Path(base_dir).absolute()
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def compile_distributed(
        self, 
        primitives: PrimitiveCollection,
        config: Optional[dict] = None
    ) -> CompilationResult:
        """Compile primitives into distributed AGENTS.md files.
        
        Args:
            primitives (PrimitiveCollection): Collection of primitives to compile.
            config (Optional[dict]): Configuration for distributed compilation.
        
        Returns:
            CompilationResult: Result of the distributed compilation.
        """
        self.warnings.clear()
        self.errors.clear()
        
        try:
            # Configuration with defaults aligned to Minimal Context Principle
            config = config or {}
            min_instructions = config.get('min_instructions_per_file', 1)  # Default to 1 for minimal context
            max_depth = config.get('max_depth', 4)
            source_attribution = config.get('source_attribution', True)
            
            # Phase 1: Directory structure analysis
            directory_map = self.analyze_directory_structure(primitives.instructions)
            
            # Phase 2: Determine optimal AGENTS.md placement
            placement_map = self.determine_agents_placement(
                primitives.instructions, 
                directory_map,
                min_instructions=min_instructions,
                max_depth=max_depth
            )
            
            # Phase 3: Generate distributed AGENTS.md files
            placements = self.generate_distributed_agents_files(
                placement_map,
                primitives,
                source_attribution=source_attribution
            )
            
            # Phase 4: Validate coverage
            coverage_validation = self._validate_coverage(placements, primitives.instructions)
            if coverage_validation:
                self.warnings.extend(coverage_validation)
            
            # Compile statistics
            stats = self._compile_distributed_stats(placements, primitives)
            
            return CompilationResult(
                success=len(self.errors) == 0,
                placements=placements,
                content_map={p.agents_path: self._generate_agents_content(p, primitives) for p in placements},
                warnings=self.warnings.copy(),
                errors=self.errors.copy(),
                stats=stats
            )
            
        except Exception as e:
            self.errors.append(f"Distributed compilation failed: {str(e)}")
            return CompilationResult(
                success=False,
                placements=[],
                content_map={},
                warnings=self.warnings.copy(),
                errors=self.errors.copy(),
                stats={}
            )
    
    def analyze_directory_structure(self, instructions: List[Instruction]) -> DirectoryMap:
        """Analyze project directory structure based on instruction patterns.
        
        Args:
            instructions (List[Instruction]): List of instructions to analyze.
        
        Returns:
            DirectoryMap: Analysis of the directory structure.
        """
        directories: Dict[Path, Set[str]] = defaultdict(set)
        depth_map: Dict[Path, int] = {}
        parent_map: Dict[Path, Optional[Path]] = {}
        
        # Analyze each instruction's applyTo pattern
        for instruction in instructions:
            if not instruction.apply_to:
                continue
            
            pattern = instruction.apply_to
            
            # Extract directory paths from pattern
            dirs = self._extract_directories_from_pattern(pattern)
            
            for dir_path in dirs:
                abs_dir = self.base_dir / dir_path
                directories[abs_dir].add(pattern)
                
                # Calculate depth and parent relationships
                depth = len(abs_dir.relative_to(self.base_dir).parts)
                depth_map[abs_dir] = depth
                
                if depth > 0:
                    parent_dir = abs_dir.parent
                    parent_map[abs_dir] = parent_dir
                    # Ensure parent is also tracked
                    if parent_dir not in directories:
                        directories[parent_dir] = set()
                else:
                    parent_map[abs_dir] = None
        
        # Add base directory
        directories[self.base_dir].update(instruction.apply_to for instruction in instructions if instruction.apply_to)
        depth_map[self.base_dir] = 0
        parent_map[self.base_dir] = None
        
        return DirectoryMap(
            directories=dict(directories),
            depth_map=depth_map,
            parent_map=parent_map
        )
    
    def determine_agents_placement(
        self, 
        instructions: List[Instruction],
        directory_map: DirectoryMap,
        min_instructions: int = 1,
        max_depth: int = 4
    ) -> Dict[Path, List[Instruction]]:
        """Determine optimal AGENTS.md file placement based on patterns and structure.
        
        Following the Minimal Context Principle, creates focused AGENTS.md files 
        in each directory that has applicable instructions, avoiding context bloat.
        
        Args:
            instructions (List[Instruction]): List of instructions to place.
            directory_map (DirectoryMap): Directory structure analysis.
            min_instructions (int): Minimum instructions (default 1 for minimal context).
            max_depth (int): Maximum depth for placement.
        
        Returns:
            Dict[Path, List[Instruction]]: Mapping of directory paths to instructions.
        """
        placement_map: Dict[Path, List[Instruction]] = defaultdict(list)
        
        # Group instructions by their most specific applicable directory
        for instruction in instructions:
            if not instruction.apply_to:
                # Instructions without patterns go to root
                placement_map[self.base_dir].append(instruction)
                continue
            
            # Find the most specific directory for this instruction
            best_dir = self._find_best_directory(instruction, directory_map, max_depth)
            placement_map[best_dir].append(instruction)
        
        # Minimal Context Principle: Create AGENTS.md for every directory with instructions
        # This ensures focused, minimal context files rather than consolidating upward
        final_placement = {}
        for dir_path, dir_instructions in placement_map.items():
            if dir_instructions:  # Create AGENTS.md if any instructions apply
                final_placement[dir_path] = dir_instructions
        
        return final_placement
    
    def generate_distributed_agents_files(
        self,
        placement_map: Dict[Path, List[Instruction]],
        primitives: PrimitiveCollection,
        source_attribution: bool = True
    ) -> List[PlacementResult]:
        """Generate distributed AGENTS.md file contents.
        
        Args:
            placement_map (Dict[Path, List[Instruction]]): Directory to instructions mapping.
            primitives (PrimitiveCollection): Full primitive collection.
            source_attribution (bool): Whether to include source attribution.
        
        Returns:
            List[PlacementResult]: List of placement results with content.
        """
        placements = []
        
        for dir_path, instructions in placement_map.items():
            agents_path = dir_path / "AGENTS.md"
            
            # Build source attribution map if enabled
            source_map = {}
            if source_attribution:
                for instruction in instructions:
                    source_info = getattr(instruction, 'source', 'local')
                    source_map[str(instruction.file_path)] = source_info
            
            # Extract coverage patterns
            patterns = set()
            for instruction in instructions:
                if instruction.apply_to:
                    patterns.add(instruction.apply_to)
            
            placement = PlacementResult(
                agents_path=agents_path,
                instructions=instructions,
                coverage_patterns=patterns,
                source_attribution=source_map
            )
            
            placements.append(placement)
        
        return placements
    
    def _extract_directories_from_pattern(self, pattern: str) -> List[Path]:
        """Extract potential directory paths from a file pattern.
        
        Args:
            pattern (str): File pattern like "src/**/*.py" or "docs/*.md"
        
        Returns:
            List[Path]: List of directory paths that could contain matching files.
        """
        directories = []
        
        # Remove filename part and wildcards to get directory structure
        # Examples:
        # "src/**/*.py" -> ["src"] 
        # "docs/*.md" -> ["docs"]
        # "**/*.py" -> ["."] (current directory)
        # "*.py" -> ["."] (current directory)
        
        if pattern.startswith("**/"):
            # Global pattern - applies to all directories
            directories.append(Path("."))
        elif "/" in pattern:
            # Extract directory part
            dir_part = pattern.split("/")[0]
            if not dir_part.startswith("*"):
                directories.append(Path(dir_part))
            else:
                directories.append(Path("."))
        else:
            # No directory part - applies to current directory
            directories.append(Path("."))
        
        return directories
    
    def _find_best_directory(
        self, 
        instruction: Instruction, 
        directory_map: DirectoryMap,
        max_depth: int
    ) -> Path:
        """Find the best directory for placing an instruction.
        
        Args:
            instruction (Instruction): Instruction to place.
            directory_map (DirectoryMap): Directory structure analysis.
            max_depth (int): Maximum allowed depth.
        
        Returns:
            Path: Best directory path for the instruction.
        """
        if not instruction.apply_to:
            return self.base_dir
        
        pattern = instruction.apply_to
        best_dir = self.base_dir
        best_specificity = 0
        
        for dir_path in directory_map.directories:
            # Skip directories that are too deep
            if directory_map.depth_map.get(dir_path, 0) > max_depth:
                continue
            
            # Check if this directory could contain files matching the pattern
            if pattern in directory_map.directories[dir_path]:
                # Prefer more specific (deeper) directories
                specificity = directory_map.depth_map.get(dir_path, 0)
                if specificity > best_specificity:
                    best_specificity = specificity
                    best_dir = dir_path
        
        return best_dir
    
    def _generate_agents_content(
        self, 
        placement: PlacementResult, 
        primitives: PrimitiveCollection
    ) -> str:
        """Generate AGENTS.md content for a specific placement.
        
        Args:
            placement (PlacementResult): Placement result with instructions.
            primitives (PrimitiveCollection): Full primitive collection.
        
        Returns:
            str: Generated AGENTS.md content.
        """
        sections = []
        
        # Header with source attribution
        sections.append("# AGENTS.md")
        sections.append("<!-- Generated by APM CLI from distributed .apm/ primitives -->")
        sections.append(BUILD_ID_PLACEHOLDER)
        sections.append(f"<!-- APM Version: {get_version()} -->")
        
        # Add source attribution summary if enabled
        if placement.source_attribution:
            sources = set(placement.source_attribution.values())
            if len(sources) > 1:
                sections.append(f"<!-- Sources: {', '.join(sorted(sources))} -->")
            else:
                sections.append(f"<!-- Source: {list(sources)[0] if sources else 'local'} -->")
        
        sections.append("")
        
        # Group instructions by pattern
        pattern_groups: Dict[str, List[Instruction]] = defaultdict(list)
        for instruction in placement.instructions:
            if instruction.apply_to:
                pattern_groups[instruction.apply_to].append(instruction)
        
        # Generate sections for each pattern
        for pattern, pattern_instructions in sorted(pattern_groups.items()):
            sections.append(f"## Files matching `{pattern}`")
            sections.append("")
            
            for instruction in pattern_instructions:
                content = instruction.content.strip()
                if content:
                    # Add source attribution for individual instructions
                    if placement.source_attribution:
                        source = placement.source_attribution.get(str(instruction.file_path), 'local')
                        try:
                            rel_path = instruction.file_path.relative_to(self.base_dir)
                        except ValueError:
                            rel_path = instruction.file_path
                        
                        sections.append(f"<!-- Source: {source} {rel_path} -->")
                    
                    sections.append(content)
                    sections.append("")
        
        # Footer
        sections.append("---")
        sections.append("*This file was generated by APM CLI. Do not edit manually.*")
        sections.append("*To regenerate: `apm compile`*")
        sections.append("")
        
        return "\n".join(sections)
    
    def _validate_coverage(
        self, 
        placements: List[PlacementResult], 
        all_instructions: List[Instruction]
    ) -> List[str]:
        """Validate that all instructions are covered by placements.
        
        Args:
            placements (List[PlacementResult]): Generated placements.
            all_instructions (List[Instruction]): All available instructions.
        
        Returns:
            List[str]: List of coverage warnings.
        """
        warnings = []
        placed_instructions = set()
        
        for placement in placements:
            placed_instructions.update(str(inst.file_path) for inst in placement.instructions)
        
        all_instruction_paths = set(str(inst.file_path) for inst in all_instructions)
        
        missing_instructions = all_instruction_paths - placed_instructions
        if missing_instructions:
            warnings.append(f"Instructions not placed in any AGENTS.md: {', '.join(missing_instructions)}")
        
        return warnings
    
    def _compile_distributed_stats(
        self, 
        placements: List[PlacementResult], 
        primitives: PrimitiveCollection
    ) -> Dict[str, int]:
        """Compile statistics about the distributed compilation.
        
        Args:
            placements (List[PlacementResult]): Generated placements.
            primitives (PrimitiveCollection): Full primitive collection.
        
        Returns:
            Dict[str, int]: Compilation statistics.
        """
        total_instructions = sum(len(p.instructions) for p in placements)
        total_patterns = sum(len(p.coverage_patterns) for p in placements)
        
        return {
            "agents_files_generated": len(placements),
            "total_instructions_placed": total_instructions,
            "total_patterns_covered": total_patterns,
            "primitives_found": primitives.count(),
            "chatmodes": len(primitives.chatmodes),
            "instructions": len(primitives.instructions),
            "contexts": len(primitives.contexts)
        }