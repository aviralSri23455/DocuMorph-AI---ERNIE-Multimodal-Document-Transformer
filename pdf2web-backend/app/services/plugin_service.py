"""Plugin System Service for extensible widget types."""
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from loguru import logger
from pydantic import BaseModel

from app.config import settings


class PluginType(str, Enum):
    """Types of plugins."""
    WIDGET = "widget"  # Interactive component (timeline, map, etc.)
    PROCESSOR = "processor"  # Content processor
    EXPORTER = "exporter"  # Export format
    THEME = "theme"  # Custom theme


class PluginStatus(str, Enum):
    """Plugin status."""
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


class PluginManifest(BaseModel):
    """Plugin manifest definition."""
    name: str
    version: str
    type: PluginType
    description: str
    author: Optional[str] = None
    entry_point: str  # Main module/function
    dependencies: List[str] = []
    config_schema: Dict[str, Any] = {}
    assets: List[str] = []  # CSS/JS files to include


class PluginInfo(BaseModel):
    """Plugin information."""
    manifest: PluginManifest
    status: PluginStatus
    path: str
    error_message: Optional[str] = None


class BasePlugin:
    """Base class for all plugins."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    def render(self, content: str, block_id: str, **kwargs) -> str:
        """Render the plugin output. Override in subclass."""
        raise NotImplementedError
    
    def get_assets(self) -> Dict[str, List[str]]:
        """Return CSS and JS assets needed. Override in subclass."""
        return {"css": [], "js": []}
    
    def validate_content(self, content: str) -> bool:
        """Validate if content is suitable for this plugin."""
        return True


class TimelinePlugin(BasePlugin):
    """Built-in Timeline widget plugin."""
    
    def render(self, content: str, block_id: str, **kwargs) -> str:
        """Render timeline from list content."""
        events = self._parse_events(content)
        style = kwargs.get("style", settings.timeline_default_style)
        
        events_html = ""
        for i, event in enumerate(events):
            events_html += f'''
            <div class="timeline-item {'left' if i % 2 == 0 else 'right'}">
                <div class="timeline-content">
                    <div class="timeline-date">{event.get('date', '')}</div>
                    <div class="timeline-title">{event.get('title', '')}</div>
                    <div class="timeline-desc">{event.get('description', '')}</div>
                </div>
            </div>
            '''
        
        return f'''
        <div class="timeline-container timeline-{style}" id="timeline-{block_id}">
            <div class="timeline-line"></div>
            {events_html}
        </div>
        '''
    
    def _parse_events(self, content: str) -> List[Dict[str, str]]:
        """Parse timeline events from content."""
        events = []
        lines = content.strip().split("\n")
        
        current_event = {}
        for line in lines:
            line = line.strip().lstrip("-*•").strip()
            if not line:
                if current_event:
                    events.append(current_event)
                    current_event = {}
                continue
            
            # Try to parse date: title format
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    # Check if first part looks like a date
                    if any(c.isdigit() for c in parts[0]):
                        current_event["date"] = parts[0].strip()
                        current_event["title"] = parts[1].strip()
                    else:
                        current_event["title"] = line
            else:
                if "title" not in current_event:
                    current_event["title"] = line
                else:
                    current_event["description"] = current_event.get("description", "") + " " + line
        
        if current_event:
            events.append(current_event)
        
        return events
    
    def get_assets(self) -> Dict[str, List[str]]:
        return {
            "css": [self._get_timeline_css()],
            "js": []
        }
    
    def _get_timeline_css(self) -> str:
        return '''
        .timeline-container { position: relative; padding: 20px 0; }
        .timeline-line { position: absolute; left: 50%; width: 2px; height: 100%; background: #ddd; transform: translateX(-50%); }
        .timeline-item { position: relative; margin: 20px 0; width: 50%; padding: 0 30px; }
        .timeline-item.left { left: 0; text-align: right; }
        .timeline-item.right { left: 50%; text-align: left; }
        .timeline-content { background: #f9f9f9; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .timeline-date { font-size: 12px; color: #666; margin-bottom: 5px; }
        .timeline-title { font-weight: 600; margin-bottom: 5px; }
        .timeline-desc { font-size: 14px; color: #555; }
        .timeline-horizontal .timeline-line { top: 50%; left: 0; width: 100%; height: 2px; transform: translateY(-50%); }
        .timeline-horizontal .timeline-item { display: inline-block; width: auto; vertical-align: top; }
        @media (max-width: 768px) {
            .timeline-line { left: 20px; }
            .timeline-item { width: 100%; left: 0 !important; text-align: left !important; padding-left: 50px; }
        }
        '''


class MapPlugin(BasePlugin):
    """Built-in Map widget plugin using Leaflet."""
    
    def render(self, content: str, block_id: str, **kwargs) -> str:
        """Render map from location data."""
        locations = self._parse_locations(content)
        provider = kwargs.get("provider", settings.map_default_provider)
        
        markers_js = ""
        bounds = []
        for loc in locations:
            lat, lng = loc.get("lat", 0), loc.get("lng", 0)
            name = loc.get("name", "")
            markers_js += f'L.marker([{lat}, {lng}]).addTo(map_{block_id.replace("-", "_")}).bindPopup("{name}");\n'
            bounds.append([lat, lng])
        
        # Calculate center
        if bounds:
            center_lat = sum(b[0] for b in bounds) / len(bounds)
            center_lng = sum(b[1] for b in bounds) / len(bounds)
        else:
            center_lat, center_lng = 0, 0
        
        return f'''
        <div class="map-container" id="map-{block_id}" style="height: 400px; width: 100%;"></div>
        <script>
        (function() {{
            var map_{block_id.replace("-", "_")} = L.map('map-{block_id}').setView([{center_lat}, {center_lng}], 10);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map_{block_id.replace("-", "_")});
            {markers_js}
        }})();
        </script>
        '''
    
    def _parse_locations(self, content: str) -> List[Dict[str, Any]]:
        """Parse location data from content."""
        locations = []
        lines = content.strip().split("\n")
        
        for line in lines:
            line = line.strip().lstrip("-*•").strip()
            if not line:
                continue
            
            # Try to parse: name (lat, lng) or name: lat, lng
            import re
            
            # Pattern: Name (lat, lng)
            match = re.search(r'(.+?)\s*\(?\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)?', line)
            if match:
                locations.append({
                    "name": match.group(1).strip().rstrip(":"),
                    "lat": float(match.group(2)),
                    "lng": float(match.group(3))
                })
        
        return locations
    
    def get_assets(self) -> Dict[str, List[str]]:
        return {
            "css": ['<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">'],
            "js": ['<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>']
        }


class PluginService:
    """Service for managing plugins."""
    
    def __init__(self):
        self.plugins_dir = settings.plugins_dir
        self._plugins: Dict[str, PluginInfo] = {}
        self._instances: Dict[str, BasePlugin] = {}
        self._builtin_plugins = {
            "timeline": TimelinePlugin,
            "map": MapPlugin
        }
        
        if settings.enable_plugins:
            self._load_builtin_plugins()
            self._discover_plugins()
    
    def _load_builtin_plugins(self):
        """Load built-in plugins."""
        if settings.enable_timeline_widget:
            self._instances["timeline"] = TimelinePlugin()
            self._plugins["timeline"] = PluginInfo(
                manifest=PluginManifest(
                    name="timeline",
                    version="1.0.0",
                    type=PluginType.WIDGET,
                    description="Timeline visualization widget",
                    entry_point="builtin"
                ),
                status=PluginStatus.ACTIVE,
                path="builtin"
            )
        
        if settings.enable_map_widget:
            self._instances["map"] = MapPlugin()
            self._plugins["map"] = PluginInfo(
                manifest=PluginManifest(
                    name="map",
                    version="1.0.0",
                    type=PluginType.WIDGET,
                    description="Interactive map widget using Leaflet",
                    entry_point="builtin"
                ),
                status=PluginStatus.ACTIVE,
                path="builtin"
            )
    
    def _discover_plugins(self):
        """Discover and load plugins from plugins directory."""
        if not self.plugins_dir.exists():
            return
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                manifest_path = plugin_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        self._load_plugin(plugin_dir, manifest_path)
                    except Exception as e:
                        logger.error(f"Failed to load plugin {plugin_dir.name}: {e}")
    
    def _load_plugin(self, plugin_dir: Path, manifest_path: Path):
        """Load a single plugin."""
        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)
        
        manifest = PluginManifest(**manifest_data)
        
        # Check if plugin is enabled
        if manifest.name not in settings.enabled_plugins_list:
            self._plugins[manifest.name] = PluginInfo(
                manifest=manifest,
                status=PluginStatus.DISABLED,
                path=str(plugin_dir)
            )
            return
        
        # Load plugin module
        entry_point = plugin_dir / manifest.entry_point
        if entry_point.exists():
            spec = importlib.util.spec_from_file_location(manifest.name, entry_point)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get plugin class
            plugin_class = getattr(module, "Plugin", None)
            if plugin_class and issubclass(plugin_class, BasePlugin):
                self._instances[manifest.name] = plugin_class()
                self._plugins[manifest.name] = PluginInfo(
                    manifest=manifest,
                    status=PluginStatus.ACTIVE,
                    path=str(plugin_dir)
                )
                logger.info(f"Loaded plugin: {manifest.name} v{manifest.version}")
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get a plugin instance by name."""
        return self._instances.get(name)
    
    def list_plugins(self) -> List[PluginInfo]:
        """List all discovered plugins."""
        return list(self._plugins.values())
    
    def get_active_plugins(self) -> List[str]:
        """Get names of active plugins."""
        return [name for name, info in self._plugins.items() if info.status == PluginStatus.ACTIVE]
    
    def render_widget(
        self,
        plugin_name: str,
        content: str,
        block_id: str,
        **kwargs
    ) -> Optional[str]:
        """Render content using a widget plugin."""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            logger.warning(f"Plugin not found: {plugin_name}")
            return None
        
        try:
            return plugin.render(content, block_id, **kwargs)
        except Exception as e:
            logger.error(f"Plugin render error ({plugin_name}): {e}")
            return None
    
    def get_all_assets(self) -> Dict[str, List[str]]:
        """Get all CSS and JS assets from active plugins."""
        all_css = []
        all_js = []
        
        for name in self.get_active_plugins():
            plugin = self.get_plugin(name)
            if plugin:
                assets = plugin.get_assets()
                all_css.extend(assets.get("css", []))
                all_js.extend(assets.get("js", []))
        
        return {"css": all_css, "js": all_js}
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin."""
        if name in self._plugins:
            info = self._plugins[name]
            if info.status == PluginStatus.DISABLED:
                # Reload plugin
                plugin_dir = Path(info.path)
                manifest_path = plugin_dir / "manifest.json"
                if manifest_path.exists():
                    self._load_plugin(plugin_dir, manifest_path)
                    return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin."""
        if name in self._plugins and name in self._instances:
            self._plugins[name].status = PluginStatus.DISABLED
            del self._instances[name]
            return True
        return False


# Singleton instance
plugin_service = PluginService()
