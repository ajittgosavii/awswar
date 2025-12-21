"""
Architecture Diagram Generator Module
=====================================
Extracted from architecture_designer_revamped.py for better maintainability.

This module handles the generation of architecture diagrams including:
- SVG diagram generation
- Component placement and sizing
- Connection routing
- Export functionality
"""

import math
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# ============================================================================
# CONSTANTS
# ============================================================================

# AWS Service Icons (simplified SVG paths)
AWS_SERVICE_COLORS = {
    'compute': '#FF9900',      # Orange
    'storage': '#3F8624',      # Green
    'database': '#3B48CC',     # Blue
    'networking': '#8C4FFF',   # Purple
    'security': '#DD344C',     # Red
    'analytics': '#00A1C9',    # Cyan
    'integration': '#E7157B',  # Pink
    'management': '#7AA116',   # Olive
    'default': '#232F3E'       # AWS Dark
}

AWS_SERVICE_CATEGORIES = {
    'ec2': 'compute', 'lambda': 'compute', 'ecs': 'compute', 'eks': 'compute',
    'fargate': 'compute', 'batch': 'compute', 'lightsail': 'compute',
    's3': 'storage', 'ebs': 'storage', 'efs': 'storage', 'glacier': 'storage',
    'fsx': 'storage', 'backup': 'storage',
    'rds': 'database', 'dynamodb': 'database', 'elasticache': 'database',
    'redshift': 'database', 'neptune': 'database', 'documentdb': 'database',
    'aurora': 'database', 'timestream': 'database',
    'vpc': 'networking', 'cloudfront': 'networking', 'route53': 'networking',
    'elb': 'networking', 'alb': 'networking', 'nlb': 'networking',
    'api_gateway': 'networking', 'direct_connect': 'networking',
    'iam': 'security', 'cognito': 'security', 'waf': 'security',
    'shield': 'security', 'kms': 'security', 'secrets_manager': 'security',
    'guardduty': 'security', 'inspector': 'security', 'macie': 'security',
    'kinesis': 'analytics', 'athena': 'analytics', 'emr': 'analytics',
    'glue': 'analytics', 'quicksight': 'analytics', 'opensearch': 'analytics',
    'sqs': 'integration', 'sns': 'integration', 'eventbridge': 'integration',
    'step_functions': 'integration', 'mq': 'integration', 'appsync': 'integration',
    'cloudwatch': 'management', 'cloudtrail': 'management', 'config': 'management',
    'systems_manager': 'management', 'organizations': 'management'
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class DiagramComponent:
    """Represents a component in the architecture diagram"""
    id: str
    service_type: str
    name: str
    x: float = 0
    y: float = 0
    width: float = 120
    height: float = 80
    layer: str = 'application'
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def category(self) -> str:
        """Get the service category for coloring"""
        return AWS_SERVICE_CATEGORIES.get(self.service_type.lower(), 'default')
    
    @property
    def color(self) -> str:
        """Get the color based on service category"""
        return AWS_SERVICE_COLORS.get(self.category, AWS_SERVICE_COLORS['default'])
    
    @property
    def center(self) -> Tuple[float, float]:
        """Get center point of component"""
        return (self.x + self.width / 2, self.y + self.height / 2)


@dataclass
class DiagramConnection:
    """Represents a connection between components"""
    source_id: str
    target_id: str
    label: str = ''
    connection_type: str = 'sync'  # sync, async, data
    bidirectional: bool = False
    
    @property
    def line_style(self) -> str:
        """Get SVG line style based on connection type"""
        styles = {
            'sync': 'stroke-dasharray: none',
            'async': 'stroke-dasharray: 5,5',
            'data': 'stroke-dasharray: 10,5'
        }
        return styles.get(self.connection_type, styles['sync'])


@dataclass
class DiagramLayer:
    """Represents a layer/zone in the architecture"""
    id: str
    name: str
    y_start: float
    height: float
    color: str = '#f5f5f5'


# ============================================================================
# DIAGRAM GENERATOR
# ============================================================================

class ArchitectureDiagramGenerator:
    """
    Generates SVG architecture diagrams from component definitions.
    
    Features:
    - Automatic component layout
    - Layer-based organization
    - Connection routing
    - Export to SVG
    """
    
    # Default canvas settings
    DEFAULT_WIDTH = 1200
    DEFAULT_HEIGHT = 800
    PADDING = 50
    COMPONENT_SPACING = 30
    LAYER_PADDING = 20
    
    def __init__(self, width: int = None, height: int = None):
        """Initialize the diagram generator"""
        self.width = width or self.DEFAULT_WIDTH
        self.height = height or self.DEFAULT_HEIGHT
        self.components: Dict[str, DiagramComponent] = {}
        self.connections: List[DiagramConnection] = []
        self.layers: List[DiagramLayer] = []
        
        # Initialize default layers
        self._init_default_layers()
    
    def _init_default_layers(self):
        """Initialize default architecture layers"""
        layer_height = (self.height - 2 * self.PADDING) / 4
        
        self.layers = [
            DiagramLayer('presentation', 'Presentation Layer', 
                        self.PADDING, layer_height, '#e3f2fd'),
            DiagramLayer('application', 'Application Layer',
                        self.PADDING + layer_height, layer_height, '#f3e5f5'),
            DiagramLayer('data', 'Data Layer',
                        self.PADDING + 2 * layer_height, layer_height, '#e8f5e9'),
            DiagramLayer('infrastructure', 'Infrastructure Layer',
                        self.PADDING + 3 * layer_height, layer_height, '#fff3e0'),
        ]
    
    def add_component(self, component: DiagramComponent) -> str:
        """Add a component to the diagram"""
        if not component.id:
            component.id = self._generate_id(component.name)
        
        self.components[component.id] = component
        return component.id
    
    def add_connection(self, connection: DiagramConnection):
        """Add a connection between components"""
        if connection.source_id in self.components and connection.target_id in self.components:
            self.connections.append(connection)
    
    def _generate_id(self, name: str) -> str:
        """Generate a unique ID from a name"""
        base = name.lower().replace(' ', '_')
        hash_suffix = hashlib.md5(name.encode()).hexdigest()[:6]
        return f"{base}_{hash_suffix}"
    
    def auto_layout(self):
        """Automatically arrange components within their layers"""
        # Group components by layer
        layer_components: Dict[str, List[DiagramComponent]] = {
            layer.id: [] for layer in self.layers
        }
        
        for component in self.components.values():
            layer_id = component.layer
            if layer_id in layer_components:
                layer_components[layer_id].append(component)
            else:
                layer_components['application'].append(component)
        
        # Position components within each layer
        for layer in self.layers:
            components = layer_components[layer.id]
            if not components:
                continue
            
            # Calculate available width
            available_width = self.width - 2 * self.PADDING - 2 * self.LAYER_PADDING
            
            # Calculate component positions
            total_width = sum(c.width for c in components) + \
                         self.COMPONENT_SPACING * (len(components) - 1)
            
            start_x = self.PADDING + self.LAYER_PADDING + \
                     (available_width - total_width) / 2
            
            current_x = start_x
            for component in components:
                component.x = current_x
                component.y = layer.y_start + (layer.height - component.height) / 2
                current_x += component.width + self.COMPONENT_SPACING
    
    def generate_svg(self) -> str:
        """Generate the complete SVG diagram"""
        # Auto-layout if not already done
        self.auto_layout()
        
        svg_parts = [
            self._svg_header(),
            self._svg_defs(),
            self._svg_layers(),
            self._svg_connections(),
            self._svg_components(),
            self._svg_footer()
        ]
        
        return '\n'.join(svg_parts)
    
    def _svg_header(self) -> str:
        """Generate SVG header"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{self.width}" height="{self.height}"
     viewBox="0 0 {self.width} {self.height}">
<style>
    .component {{ font-family: Arial, sans-serif; }}
    .component-label {{ font-size: 12px; fill: #333; text-anchor: middle; }}
    .layer-label {{ font-size: 14px; fill: #666; font-weight: bold; }}
    .connection {{ fill: none; stroke: #666; stroke-width: 2; }}
    .connection-label {{ font-size: 10px; fill: #666; }}
</style>'''
    
    def _svg_defs(self) -> str:
        """Generate SVG definitions (markers, gradients)"""
        return '''
<defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" 
            refX="9" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="#666"/>
    </marker>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="2" dy="2" stdDeviation="2" flood-opacity="0.3"/>
    </filter>
</defs>'''
    
    def _svg_layers(self) -> str:
        """Generate SVG for layers"""
        parts = []
        for layer in self.layers:
            parts.append(f'''
<g class="layer" id="layer-{layer.id}">
    <rect x="{self.PADDING}" y="{layer.y_start}" 
          width="{self.width - 2 * self.PADDING}" height="{layer.height}"
          fill="{layer.color}" stroke="#ddd" stroke-width="1" rx="5"/>
    <text x="{self.PADDING + 10}" y="{layer.y_start + 20}" 
          class="layer-label">{layer.name}</text>
</g>''')
        return '\n'.join(parts)
    
    def _svg_connections(self) -> str:
        """Generate SVG for connections"""
        parts = []
        for conn in self.connections:
            source = self.components.get(conn.source_id)
            target = self.components.get(conn.target_id)
            
            if not source or not target:
                continue
            
            # Calculate connection points
            sx, sy = source.center
            tx, ty = target.center
            
            # Simple straight line for now
            parts.append(f'''
<g class="connection-group">
    <line x1="{sx}" y1="{sy}" x2="{tx}" y2="{ty}" 
          class="connection" style="{conn.line_style}"
          marker-end="url(#arrowhead)"/>
</g>''')
            
            # Add label if present
            if conn.label:
                mx, my = (sx + tx) / 2, (sy + ty) / 2
                parts.append(f'''
    <text x="{mx}" y="{my - 5}" class="connection-label">{conn.label}</text>''')
        
        return '\n'.join(parts)
    
    def _svg_components(self) -> str:
        """Generate SVG for components"""
        parts = []
        for component in self.components.values():
            parts.append(f'''
<g class="component" id="{component.id}" filter="url(#shadow)">
    <rect x="{component.x}" y="{component.y}" 
          width="{component.width}" height="{component.height}"
          fill="white" stroke="{component.color}" stroke-width="3" rx="8"/>
    <rect x="{component.x}" y="{component.y}" 
          width="{component.width}" height="25"
          fill="{component.color}" rx="8"/>
    <rect x="{component.x}" y="{component.y + 17}" 
          width="{component.width}" height="8"
          fill="{component.color}"/>
    <text x="{component.x + component.width/2}" y="{component.y + 17}" 
          class="component-label" fill="white" font-weight="bold">
        {component.service_type.upper()}
    </text>
    <text x="{component.x + component.width/2}" y="{component.y + component.height/2 + 15}" 
          class="component-label">{component.name}</text>
</g>''')
        return '\n'.join(parts)
    
    def _svg_footer(self) -> str:
        """Generate SVG footer"""
        return '</svg>'
    
    def export_to_file(self, filepath: str):
        """Export diagram to SVG file"""
        svg_content = self.generate_svg()
        with open(filepath, 'w') as f:
            f.write(svg_content)


# ============================================================================
# QUICK DIAGRAM BUILDER
# ============================================================================

class QuickDiagramBuilder:
    """
    Simplified interface for quickly building architecture diagrams.
    
    Example:
        builder = QuickDiagramBuilder()
        builder.add_service('alb', 'Load Balancer', 'presentation')
        builder.add_service('ecs', 'API Service', 'application')
        builder.add_service('rds', 'Database', 'data')
        builder.connect('alb', 'ecs')
        builder.connect('ecs', 'rds')
        svg = builder.build()
    """
    
    def __init__(self, title: str = "Architecture Diagram"):
        self.title = title
        self.generator = ArchitectureDiagramGenerator()
        self._service_counter = {}
    
    def add_service(self, service_type: str, name: str, 
                   layer: str = 'application') -> str:
        """Add a service to the diagram"""
        # Generate unique ID
        count = self._service_counter.get(service_type, 0)
        self._service_counter[service_type] = count + 1
        component_id = f"{service_type}_{count}"
        
        component = DiagramComponent(
            id=component_id,
            service_type=service_type,
            name=name,
            layer=layer
        )
        
        self.generator.add_component(component)
        return component_id
    
    def connect(self, source: str, target: str, 
                label: str = '', connection_type: str = 'sync'):
        """Connect two services"""
        # Find components by service type prefix if not exact match
        source_id = self._find_component(source)
        target_id = self._find_component(target)
        
        if source_id and target_id:
            self.generator.add_connection(DiagramConnection(
                source_id=source_id,
                target_id=target_id,
                label=label,
                connection_type=connection_type
            ))
    
    def _find_component(self, identifier: str) -> Optional[str]:
        """Find component ID by identifier or prefix"""
        if identifier in self.generator.components:
            return identifier
        
        # Try to find by service type prefix
        for comp_id in self.generator.components:
            if comp_id.startswith(identifier):
                return comp_id
        
        return None
    
    def build(self) -> str:
        """Build and return the SVG diagram"""
        return self.generator.generate_svg()
    
    def save(self, filepath: str):
        """Save diagram to file"""
        self.generator.export_to_file(filepath)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'DiagramComponent',
    'DiagramConnection', 
    'DiagramLayer',
    'ArchitectureDiagramGenerator',
    'QuickDiagramBuilder',
    'AWS_SERVICE_COLORS',
    'AWS_SERVICE_CATEGORIES',
]
