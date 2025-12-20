"""HTML Generator Service with interactive component injection.

Generates fully functional HTML with:
- Chart.js for data visualization (bar, line, pie charts)
- Quiz.js for interactive Q&A widgets
- Prism.js for syntax highlighting
- Code execution sandbox (JavaScript)
- Timeline and Map widgets via plugins
"""
from typing import List, Dict, Any
import json
import re
from loguru import logger

from app.models.schemas import (
    ContentBlock, ContentType, SemanticSuggestion,
    ComponentSuggestion, ThemeType
)


class HTMLGenerator:
    """Service for generating HTML with interactive components."""
    
    def __init__(self):
        self.theme_styles = self._load_theme_styles()
        self.component_templates = self._load_component_templates()
    
    def _load_theme_styles(self) -> Dict[str, str]:
        """Load CSS styles for each theme."""
        base_styles = """
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; }
        .container { max-width: 900px; margin: 0 auto; padding: 20px; }
        h1, h2, h3, h4 { margin: 1.5em 0 0.5em; }
        p { margin: 1em 0; }
        table { border-collapse: collapse; width: 100%; margin: 1em 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background: #f5f5f5; font-weight: 600; }
        tr:nth-child(even) { background: #fafafa; }
        tr:hover { background: #f0f0f0; }
        ul, ol { margin: 1em 0; padding-left: 2em; }
        pre { overflow-x: auto; padding: 1em; border-radius: 8px; margin: 1em 0; }
        code { font-family: 'Fira Code', 'Consolas', monospace; }
        img { max-width: 100%; height: auto; border-radius: 4px; }
        blockquote { border-left: 4px solid #4e79a7; padding-left: 1em; margin: 1em 0; font-style: italic; color: #555; }
        .chart-container { width: 100%; max-width: 700px; margin: 2em auto; padding: 20px; background: #fff; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .chart-container canvas { max-height: 400px; }
        .quiz-container { background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%); padding: 25px; border-radius: 12px; margin: 1.5em 0; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
        .quiz-question { font-size: 1.2em; font-weight: 600; margin-bottom: 15px; color: #333; }
        .quiz-option { display: block; padding: 12px 15px; margin: 8px 0; cursor: pointer; border: 2px solid #ddd; border-radius: 8px; transition: all 0.2s ease; background: #fff; }
        .quiz-option:hover { border-color: #4e79a7; background: #f0f7ff; transform: translateX(5px); }
        .quiz-option.selected { border-color: #4e79a7; background: #e3f2fd; }
        .quiz-option.correct { border-color: #28a745; background: #d4edda; }
        .quiz-option.incorrect { border-color: #dc3545; background: #f8d7da; }
        .quiz-check-btn { margin-top: 15px; padding: 12px 24px; background: linear-gradient(135deg, #4e79a7 0%, #3d6a98 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; transition: transform 0.2s, box-shadow 0.2s; }
        .quiz-check-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(78,121,167,0.4); }
        .quiz-feedback { margin-top: 15px; padding: 12px 15px; border-radius: 8px; font-weight: 600; display: none; }
        .quiz-feedback.show { display: block; animation: fadeIn 0.3s ease; }
        .quiz-feedback.correct { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .quiz-feedback.incorrect { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .code-block { position: relative; margin: 1.5em 0; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .code-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 8px 15px; background: #2d2d2d; border-bottom: 1px solid #444; }
        .code-lang { font-size: 12px; color: #aaa; text-transform: uppercase; font-weight: 600; }
        .copy-btn { background: #444; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; transition: background 0.2s; }
        .copy-btn:hover { background: #555; }
        .copy-btn.copied { background: #28a745; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        @media (max-width: 768px) { .container { padding: 15px; } table { font-size: 14px; } .chart-container { padding: 10px; } }
        """
        
        return {
            "light": base_styles + """
                body { background: #ffffff; color: #333333; }
                a { color: #0066cc; }
                a:hover { color: #004499; }
                pre { background: #f4f4f4; border: 1px solid #e0e0e0; }
                .code-block pre { background: #1e1e1e; color: #d4d4d4; }
                th { background: #f0f0f0; }
            """,
            "dark": base_styles + """
                body { background: #1a1a2e; color: #eaeaea; }
                a { color: #6eb5ff; }
                a:hover { color: #9ecfff; }
                pre { background: #2d2d44; border: 1px solid #3d3d5c; }
                th { background: #2d2d44; color: #eaeaea; }
                td { border-color: #3d3d5c; }
                tr:nth-child(even) { background: #252538; }
                tr:hover { background: #2d2d44; }
                .quiz-container { background: linear-gradient(135deg, #2d2d44 0%, #1a1a2e 100%); }
                .quiz-question { color: #eaeaea; }
                .quiz-option { background: #252538; border-color: #3d3d5c; color: #eaeaea; }
                .quiz-option:hover { background: #3d3d5c; border-color: #6eb5ff; }
                .quiz-option.selected { background: #1e3a5f; border-color: #6eb5ff; }
                .chart-container { background: #252538; }
                blockquote { border-color: #6eb5ff; color: #aaa; }
            """,
            "professional": base_styles + """
                body { background: #fafafa; color: #2c3e50; }
                h1, h2, h3 { color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.3em; }
                a { color: #2b6cb0; }
                a:hover { color: #1a4971; }
                pre { background: #edf2f7; border: 1px solid #e2e8f0; }
                th { background: #e2e8f0; color: #1a365d; }
                .quiz-container { background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%); border: 1px solid #cbd5e0; }
                .quiz-check-btn { background: linear-gradient(135deg, #2b6cb0 0%, #1a4971 100%); }
                .chart-container { border: 1px solid #e2e8f0; }
            """,
            "academic": base_styles + """
                body { background: #fffef5; color: #333; font-family: 'Georgia', 'Times New Roman', serif; }
                h1, h2, h3 { font-family: 'Times New Roman', serif; color: #1a1a1a; }
                pre { background: #f5f5dc; border: 1px solid #d4d4aa; font-family: 'Courier New', monospace; }
                blockquote { font-family: 'Georgia', serif; border-color: #8b4513; }
                th { background: #f0ead6; }
                .quiz-container { background: #f5f5dc; border: 2px solid #d4d4aa; }
            """,
            "minimal": base_styles + """
                body { background: #fff; color: #111; }
                h1, h2, h3 { font-weight: 400; letter-spacing: -0.5px; }
                pre { background: #fafafa; border: 1px solid #eee; }
                table { border: none; }
                th, td { border: none; border-bottom: 1px solid #eee; }
                th { background: transparent; font-weight: 600; }
                .quiz-container { background: #fafafa; border: 1px solid #eee; }
                .chart-container { box-shadow: none; border: 1px solid #eee; }
            """
        }
    
    def _load_component_templates(self) -> Dict[str, str]:
        """Load HTML templates for interactive components."""
        return {
            "chart_bar": """
<div class="chart-container" id="chart-{block_id}">
    <canvas id="canvas-{block_id}"></canvas>
</div>
<script>
(function() {{
    const ctx = document.getElementById('canvas-{block_id}').getContext('2d');
    new Chart(ctx, {{
        type: 'bar',
        data: {chart_data},
        options: {{
            responsive: true,
            maintainAspectRatio: true,
            plugins: {{
                legend: {{ position: 'top', labels: {{ font: {{ size: 12 }} }} }},
                title: {{ display: true, text: '{chart_title}', font: {{ size: 16 }} }},
                tooltip: {{ enabled: true, mode: 'index', intersect: false }}
            }},
            scales: {{
                y: {{ beginAtZero: true, grid: {{ color: 'rgba(0,0,0,0.1)' }} }},
                x: {{ grid: {{ display: false }} }}
            }},
            animation: {{ duration: 1000, easing: 'easeOutQuart' }}
        }}
    }});
}})();
</script>
""",
            "chart_line": """
<div class="chart-container" id="chart-{block_id}">
    <canvas id="canvas-{block_id}"></canvas>
</div>
<script>
(function() {{
    const ctx = document.getElementById('canvas-{block_id}').getContext('2d');
    new Chart(ctx, {{
        type: 'line',
        data: {chart_data},
        options: {{
            responsive: true,
            maintainAspectRatio: true,
            plugins: {{
                legend: {{ position: 'top' }},
                title: {{ display: true, text: '{chart_title}' }}
            }},
            scales: {{
                y: {{ beginAtZero: true }},
                x: {{ grid: {{ display: false }} }}
            }},
            elements: {{
                line: {{ tension: 0.3, borderWidth: 2 }},
                point: {{ radius: 4, hoverRadius: 6 }}
            }},
            animation: {{ duration: 1000 }}
        }}
    }});
}})();
</script>
""",
            "chart_pie": """
<div class="chart-container" id="chart-{block_id}">
    <canvas id="canvas-{block_id}"></canvas>
</div>
<script>
(function() {{
    const ctx = document.getElementById('canvas-{block_id}').getContext('2d');
    new Chart(ctx, {{
        type: 'pie',
        data: {chart_data},
        options: {{
            responsive: true,
            maintainAspectRatio: true,
            plugins: {{
                legend: {{ position: 'right', labels: {{ padding: 15 }} }},
                title: {{ display: true, text: '{chart_title}' }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.raw / total) * 100).toFixed(1);
                            return context.label + ': ' + context.raw + ' (' + percentage + '%)';
                        }}
                    }}
                }}
            }},
            animation: {{ animateRotate: true, animateScale: true }}
        }}
    }});
}})();
</script>
""",
            "chart_hybrid": """
<div class="hybrid-container" id="hybrid-{block_id}">
    <div class="table-section">{table_html}</div>
    <div class="chart-section">
        <div class="chart-container">
            <canvas id="canvas-{block_id}"></canvas>
        </div>
    </div>
</div>
<script>
(function() {{
    const ctx = document.getElementById('canvas-{block_id}').getContext('2d');
    new Chart(ctx, {{
        type: '{chart_type}',
        data: {chart_data},
        options: {{
            responsive: true,
            maintainAspectRatio: true,
            plugins: {{ legend: {{ position: 'top' }} }},
            animation: {{ duration: 800 }}
        }}
    }});
}})();
</script>
""",
            "quiz": """
<div class="quiz-container" id="quiz-{block_id}" data-correct="{correct_index}">
    <div class="quiz-question">{question}</div>
    <div class="quiz-options">{options}</div>
    <button class="quiz-check-btn" onclick="checkQuiz_{block_id_safe}()">Check Answer</button>
    <div class="quiz-feedback" id="feedback-{block_id}"></div>
</div>
<script>
(function() {{
    const quizContainer = document.getElementById('quiz-{block_id}');
    const options = quizContainer.querySelectorAll('.quiz-option');
    
    options.forEach(opt => {{
        opt.addEventListener('click', function() {{
            options.forEach(o => o.classList.remove('selected', 'correct', 'incorrect'));
            this.classList.add('selected');
        }});
    }});
}})();

function checkQuiz_{block_id_safe}() {{
    const container = document.getElementById('quiz-{block_id}');
    const selected = container.querySelector('.quiz-option.selected');
    const feedback = document.getElementById('feedback-{block_id}');
    const options = container.querySelectorAll('.quiz-option');
    
    if (!selected) {{
        feedback.textContent = '⚠️ Please select an answer first';
        feedback.className = 'quiz-feedback show incorrect';
        return;
    }}
    
    const isCorrect = selected.dataset.correct === 'true';
    
    // Show correct/incorrect styling
    options.forEach(opt => {{
        if (opt.dataset.correct === 'true') {{
            opt.classList.add('correct');
        }} else if (opt === selected && !isCorrect) {{
            opt.classList.add('incorrect');
        }}
    }});
    
    if (isCorrect) {{
        feedback.innerHTML = '✅ <strong>Correct!</strong> Well done!';
        feedback.className = 'quiz-feedback show correct';
    }} else {{
        feedback.innerHTML = '❌ <strong>Not quite.</strong> The correct answer is highlighted above.';
        feedback.className = 'quiz-feedback show incorrect';
    }}
}}
</script>
""",
            "code_block": """
<div class="code-block" id="code-{block_id}">
    <div class="code-toolbar">
        <span class="code-lang">{language}</span>
        <button class="copy-btn" onclick="copyCode_{block_id_safe}(this)">📋 Copy</button>
    </div>
    <pre><code class="language-{language}">{code}</code></pre>
</div>
<script>
function copyCode_{block_id_safe}(btn) {{
    const code = document.querySelector('#code-{block_id} code').textContent;
    navigator.clipboard.writeText(code).then(() => {{
        btn.textContent = '✅ Copied!';
        btn.classList.add('copied');
        setTimeout(() => {{
            btn.textContent = '📋 Copy';
            btn.classList.remove('copied');
        }}, 2000);
    }});
}}
</script>
""",
            "code_executable": """
<div class="code-executable" id="exec-{block_id}">
    <div class="code-toolbar">
        <span class="code-lang">{language}</span>
        <button class="copy-btn" onclick="copyExec_{block_id_safe}(this)">📋 Copy</button>
        <button class="run-btn" onclick="runCode_{block_id_safe}()">▶️ Run</button>
    </div>
    <textarea class="code-editor" id="editor-{block_id}" spellcheck="false">{code}</textarea>
    <div class="code-output" id="output-{block_id}">
        <span class="output-placeholder">Click "Run" to execute code...</span>
    </div>
</div>
<style>
.code-executable {{ border: 1px solid #333; border-radius: 8px; overflow: hidden; margin: 1.5em 0; }}
.code-editor {{ width: 100%; min-height: 150px; padding: 15px; border: none; font-family: 'Fira Code', 'Consolas', monospace; font-size: 14px; resize: vertical; background: #1e1e1e; color: #d4d4d4; line-height: 1.5; }}
.code-output {{ padding: 15px; background: #0d0d0d; color: #00ff00; font-family: monospace; min-height: 50px; border-top: 1px solid #333; white-space: pre-wrap; }}
.code-output.error {{ color: #ff6b6b; }}
.code-output .output-placeholder {{ color: #666; font-style: italic; }}
.run-btn {{ background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%); color: white; border: none; padding: 6px 14px; border-radius: 4px; cursor: pointer; font-weight: 600; margin-left: 8px; }}
.run-btn:hover {{ background: linear-gradient(135deg, #34ce57 0%, #28a745 100%); }}
</style>
<script>
function copyExec_{block_id_safe}(btn) {{
    const code = document.getElementById('editor-{block_id}').value;
    navigator.clipboard.writeText(code).then(() => {{
        btn.textContent = '✅ Copied!';
        setTimeout(() => btn.textContent = '📋 Copy', 2000);
    }});
}}

function runCode_{block_id_safe}() {{
    const code = document.getElementById('editor-{block_id}').value;
    const output = document.getElementById('output-{block_id}');
    output.className = 'code-output';
    output.textContent = '';
    
    // Capture console.log output
    const logs = [];
    const originalLog = console.log;
    console.log = (...args) => {{
        logs.push(args.map(a => typeof a === 'object' ? JSON.stringify(a, null, 2) : String(a)).join(' '));
        originalLog.apply(console, args);
    }};
    
    try {{
        const result = eval(code);
        console.log = originalLog;
        
        let outputText = '';
        if (logs.length > 0) {{
            outputText = logs.join('\\n');
        }}
        if (result !== undefined) {{
            outputText += (outputText ? '\\n\\n→ ' : '→ ') + (typeof result === 'object' ? JSON.stringify(result, null, 2) : String(result));
        }}
        output.textContent = outputText || '✓ Executed successfully (no output)';
    }} catch(e) {{
        console.log = originalLog;
        output.textContent = '❌ Error: ' + e.message;
        output.className = 'code-output error';
    }}
}}
</script>
"""
        }
    
    async def generate(
        self,
        blocks: List[ContentBlock],
        theme: ThemeType,
        suggestions: List[SemanticSuggestion],
        approved_components: List[str],
        images: List[str] = None,
        chart_conversions: Dict[str, str] = None,
        quiz_enabled_blocks: List[str] = None,
        code_execution_blocks: List[str] = None,
        timeline_blocks: List[str] = None,
        map_blocks: List[str] = None
    ) -> str:
        """Generate complete HTML document with interactive components."""
        chart_conversions = chart_conversions or {}
        quiz_enabled_blocks = quiz_enabled_blocks or []
        code_execution_blocks = code_execution_blocks or []
        timeline_blocks = timeline_blocks or []
        map_blocks = map_blocks or []
        
        # Build suggestion lookup
        suggestion_map = {s.block_id: s for s in suggestions if s.block_id in approved_components}
        
        # Generate body content
        body_content = []
        for block in blocks:
            # Check for timeline widget
            if block.id in timeline_blocks:
                html = self._render_timeline(block)
            # Check for map widget
            elif block.id in map_blocks:
                html = self._render_map(block)
            # Check for chart conversion options
            elif block.id in chart_conversions:
                html = self._render_chart_with_option(
                    block, 
                    suggestion_map.get(block.id),
                    chart_conversions[block.id]
                )
            # Check for quiz-enabled lists
            elif block.id in quiz_enabled_blocks and block.type == ContentType.LIST:
                html = self._render_quiz(block, suggestion_map.get(block.id))
            # Check for executable code
            elif block.id in code_execution_blocks and block.type == ContentType.CODE:
                html = self._render_executable_code(block)
            # Standard component rendering
            elif block.id in suggestion_map:
                html = self._render_interactive_component(block, suggestion_map[block.id])
            else:
                html = self._render_block(block)
            body_content.append(html)
        
        # Determine what libraries are needed
        has_charts = any(
            s.suggestion.value.startswith("chart") for s in suggestions 
            if s.block_id in approved_components
        ) or bool(chart_conversions)
        has_code = any(
            s.suggestion in [ComponentSuggestion.CODE_BLOCK, ComponentSuggestion.CODE_EXECUTABLE] 
            for s in suggestions if s.block_id in approved_components
        ) or bool(code_execution_blocks)
        has_quiz = bool(quiz_enabled_blocks)
        has_timeline = bool(timeline_blocks)
        has_map = bool(map_blocks)
        
        # Assemble full HTML
        return self._assemble_html(
            body_content="\n".join(body_content),
            theme=theme,
            has_charts=has_charts,
            has_code=has_code,
            has_quiz=has_quiz,
            has_executable=bool(code_execution_blocks),
            has_timeline=has_timeline,
            has_map=has_map
        )
    
    def _render_block(self, block: ContentBlock) -> str:
        """Render a content block as HTML."""
        content = self._escape_html(block.content)
        
        renderers = {
            ContentType.HEADING: self._render_heading,
            ContentType.PARAGRAPH: lambda c, b: f"<p>{c}</p>",
            ContentType.TABLE: self._render_table,
            ContentType.LIST: self._render_list,
            ContentType.CODE: self._render_code,
            ContentType.IMAGE: self._render_image,
            ContentType.QUOTE: lambda c, b: f"<blockquote>{c}</blockquote>"
        }
        
        renderer = renderers.get(block.type, lambda c, b: f"<p>{c}</p>")
        return renderer(content, block)
    
    def _render_heading(self, content: str, block: ContentBlock) -> str:
        """Render heading with appropriate level."""
        font_size = block.metadata.get("font_size", 12)
        if font_size >= 24:
            return f"<h1>{content}</h1>"
        elif font_size >= 18:
            return f"<h2>{content}</h2>"
        elif font_size >= 14:
            return f"<h3>{content}</h3>"
        return f"<h4>{content}</h4>"
    
    def _render_table(self, content: str, block: ContentBlock) -> str:
        """Render table HTML."""
        lines = content.split("\n")
        rows = []
        
        for i, line in enumerate(lines):
            if "|" in line and "---" not in line:
                cells = [c.strip() for c in line.split("|") if c.strip()]
                tag = "th" if i == 0 else "td"
                row = "".join([f"<{tag}>{cell}</{tag}>" for cell in cells])
                rows.append(f"<tr>{row}</tr>")
        
        if rows:
            header = rows[0] if rows else ""
            body = "".join(rows[1:]) if len(rows) > 1 else ""
            return f"<table><thead>{header}</thead><tbody>{body}</tbody></table>"
        
        return f"<pre>{content}</pre>"
    
    def _render_list(self, content: str, block: ContentBlock) -> str:
        """Render list HTML."""
        lines = content.split("\n")
        items = []
        is_ordered = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line[0].isdigit():
                is_ordered = True
                # Remove number prefix
                line = line.lstrip("0123456789.)").strip()
            else:
                line = line.lstrip("-*•").strip()
            
            items.append(f"<li>{line}</li>")
        
        tag = "ol" if is_ordered else "ul"
        return f"<{tag}>{''.join(items)}</{tag}>"
    
    def _render_code(self, content: str, block: ContentBlock) -> str:
        """Render code block."""
        # Remove markdown code fences
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        
        return f"<pre><code>{content}</code></pre>"
    
    def _render_image(self, content: str, block: ContentBlock) -> str:
        """Render image."""
        src = block.metadata.get("image_path", content)
        alt = block.metadata.get("alt_text", "Image")
        return f'<img src="{src}" alt="{alt}" loading="lazy">'
    
    def _render_interactive_component(
        self, 
        block: ContentBlock, 
        suggestion: SemanticSuggestion
    ) -> str:
        """Render an interactive component."""
        if suggestion.suggestion in [ComponentSuggestion.CHART_BAR, ComponentSuggestion.CHART_LINE, ComponentSuggestion.CHART_PIE]:
            return self._render_chart(block, suggestion)
        elif suggestion.suggestion == ComponentSuggestion.QUIZ:
            return self._render_quiz(block, suggestion)
        elif suggestion.suggestion == ComponentSuggestion.CODE_BLOCK:
            return self._render_interactive_code(block, suggestion)
        
        return self._render_block(block)
    
    def _render_chart(self, block: ContentBlock, suggestion: SemanticSuggestion) -> str:
        """Render chart component with proper Chart.js integration."""
        chart_type = "bar"
        if suggestion.suggestion == ComponentSuggestion.CHART_LINE:
            chart_type = "line"
        elif suggestion.suggestion == ComponentSuggestion.CHART_PIE:
            chart_type = "pie"
        
        chart_data = self._parse_table_to_chart_data(block.content, chart_type)
        template_key = f"chart_{chart_type}"
        template = self.component_templates.get(template_key, self.component_templates["chart_bar"])
        
        # Generate chart title from suggestion or block metadata
        chart_title = suggestion.config.get("title", "") if suggestion.config else ""
        if not chart_title:
            # Try to extract title from first line or use generic
            first_line = block.content.split("\n")[0].strip()
            if first_line and not "|" in first_line:
                chart_title = first_line[:50]
            else:
                chart_title = f"Data Visualization (Page {block.page + 1})"
        
        return template.format(
            block_id=block.id,
            chart_data=json.dumps(chart_data),
            chart_title=chart_title
        )
    
    def _parse_table_to_chart_data(self, content: str, chart_type: str = "bar") -> Dict[str, Any]:
        """Parse table content into Chart.js data format with smart detection."""
        lines = [l.strip() for l in content.split("\n") if l.strip() and "---" not in l and l.strip() != "|"]
        
        if not lines:
            return {"labels": [], "datasets": [{"label": "Data", "data": [], "backgroundColor": self._get_chart_colors(5)}]}
        
        # Parse header for column names
        header_line = lines[0]
        headers = [c.strip() for c in header_line.split("|") if c.strip()]
        
        # Parse data rows
        labels = []
        columns_data = {h: [] for h in headers[1:]} if len(headers) > 1 else {"Value": []}
        
        for line in lines[1:]:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if not cells:
                continue
            
            # First cell is usually the label
            labels.append(cells[0])
            
            # Remaining cells are data values
            for i, cell in enumerate(cells[1:]):
                col_name = headers[i + 1] if i + 1 < len(headers) else f"Column {i + 1}"
                # Extract numeric value
                numeric_val = self._extract_numeric(cell)
                if col_name in columns_data:
                    columns_data[col_name].append(numeric_val)
                elif "Value" in columns_data:
                    columns_data["Value"].append(numeric_val)
        
        # Build datasets
        colors = self._get_chart_colors(max(len(labels), len(columns_data), 1))
        datasets = []
        
        if chart_type == "pie":
            # For pie charts, use first data column
            first_col = list(columns_data.values())[0] if columns_data else []
            datasets.append({
                "data": first_col,
                "backgroundColor": colors[:len(first_col)] if first_col else colors[:1],
                "borderColor": "#fff",
                "borderWidth": 2
            })
        else:
            # For bar/line charts, create dataset per column
            for i, (col_name, values) in enumerate(columns_data.items()):
                color = colors[i % len(colors)] if colors else "#4e79a7"
                datasets.append({
                    "label": col_name,
                    "data": values,
                    "backgroundColor": color if chart_type == "bar" else f"{color}33",
                    "borderColor": color,
                    "borderWidth": 2,
                    "fill": chart_type == "line"
                })
        
        return {"labels": labels, "datasets": datasets}
    
    def _extract_numeric(self, text: str) -> float:
        """Extract numeric value from text, handling currency, percentages, etc."""
        # Remove common formatting
        cleaned = re.sub(r'[$€£¥%,\s]', '', text)
        # Try to find a number
        match = re.search(r'-?\d+\.?\d*', cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        return 0.0
    
    def _get_chart_colors(self, count: int) -> List[str]:
        """Get a list of chart colors."""
        palette = [
            "#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f",
            "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab",
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"
        ]
        if count <= 0:
            return palette[:1]  # Return at least one color
        return (palette * ((count // len(palette)) + 1))[:count]
    
    def _render_quiz(self, block: ContentBlock, suggestion: SemanticSuggestion = None) -> str:
        """Render quiz component from Q&A list with smart answer detection."""
        lines = [l.strip() for l in block.content.split("\n") if l.strip()]
        
        if not lines:
            return self._render_list(block.content, block)
        
        # First line is the question
        question = lines[0].lstrip("-*•?").strip()
        if question.endswith("?"):
            question = question
        elif not question.endswith(":"):
            question = question + "?"
        
        # Safe block ID for JS function names
        block_id_safe = block.id.replace("-", "_")
        
        # Parse options and detect correct answer
        options = []
        correct_index = 0
        
        for i, line in enumerate(lines[1:]):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check for correct answer markers
            is_correct = False
            markers = ["(correct)", "(answer)", "✓", "✔", "★", "*correct*", "[correct]", "(✓)"]
            
            for marker in markers:
                if marker.lower() in line_stripped.lower():
                    is_correct = True
                    line_stripped = line_stripped.replace(marker, "").replace(marker.upper(), "")
                    break
            
            # Also check if line starts with * (common markdown for emphasis/correct)
            if line_stripped.startswith("**") and line_stripped.endswith("**"):
                is_correct = True
                line_stripped = line_stripped[2:-2]
            
            # Clean up list markers (a), b), 1., -, etc.)
            clean_line = re.sub(r'^[\-\*•]?\s*[a-dA-D1-4][\.\)]\s*', '', line_stripped).strip()
            clean_line = clean_line.lstrip("-*•").strip()
            
            if clean_line:
                options.append({
                    "text": clean_line,
                    "is_correct": is_correct,
                    "index": len(options)
                })
                if is_correct:
                    correct_index = len(options) - 1
        
        # If no correct answer marked, default to first option
        if not any(o["is_correct"] for o in options) and options:
            options[0]["is_correct"] = True
            correct_index = 0
        
        # Build options HTML
        options_html = ""
        for opt in options:
            correct_str = "true" if opt["is_correct"] else "false"
            letter = chr(65 + opt["index"])  # A, B, C, D...
            options_html += f'<label class="quiz-option" data-correct="{correct_str}"><strong>{letter}.</strong> {self._escape_html(opt["text"])}</label>\n'
        
        return self.component_templates["quiz"].format(
            block_id=block.id,
            block_id_safe=block_id_safe,
            question=self._escape_html(question),
            options=options_html,
            correct_index=correct_index
        )
    
    def _render_interactive_code(self, block: ContentBlock, suggestion: SemanticSuggestion) -> str:
        """Render interactive code block with copy functionality."""
        language = suggestion.config.get("language", "text")
        code = block.content.strip()
        
        # Remove markdown fences
        if code.startswith("```"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        
        # Safe block ID for JS function names
        block_id_safe = block.id.replace("-", "_")
        
        return self.component_templates["code_block"].format(
            block_id=block.id,
            block_id_safe=block_id_safe,
            language=language,
            code=self._escape_html(code)
        )
    
    def _render_executable_code(self, block: ContentBlock) -> str:
        """Render executable code block with run button."""
        code = block.content.strip()
        language = self._detect_language(code)
        
        # Remove markdown fences
        if code.startswith("```"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        
        # Safe block ID for JS function names
        block_id_safe = block.id.replace("-", "_")
        
        return self.component_templates["code_executable"].format(
            block_id=block.id,
            block_id_safe=block_id_safe,
            language=language,
            code=self._escape_html(code)
        )
    
    def _render_chart_with_option(
        self, 
        block: ContentBlock, 
        suggestion: SemanticSuggestion,
        option: str
    ) -> str:
        """Render table with chart conversion option (keep_table, convert_to_chart, hybrid)."""
        if option == "keep_table":
            return self._render_table(block.content, block)
        
        # Determine chart type
        chart_type = "bar"  # Default
        if suggestion:
            if suggestion.suggestion == ComponentSuggestion.CHART_LINE:
                chart_type = "line"
            elif suggestion.suggestion == ComponentSuggestion.CHART_PIE:
                chart_type = "pie"
        
        chart_data = self._parse_table_to_chart_data(block.content, chart_type)
        
        # Generate chart title
        chart_title = ""
        if suggestion and suggestion.config:
            chart_title = suggestion.config.get("title", "")
        if not chart_title:
            chart_title = f"Data from Page {block.page + 1}"
        
        if option == "hybrid":
            # Show both table and chart side by side
            table_html = self._render_table(block.content, block)
            return self.component_templates["chart_hybrid"].format(
                block_id=block.id,
                table_html=table_html,
                chart_type=chart_type,
                chart_data=json.dumps(chart_data),
                chart_title=chart_title
            )
        else:
            # Convert to chart only
            template_key = f"chart_{chart_type}"
            template = self.component_templates.get(template_key, self.component_templates["chart_bar"])
            return template.format(
                block_id=block.id,
                chart_data=json.dumps(chart_data),
                chart_title=chart_title
            )
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code content."""
        code_lower = code.lower()
        if "def " in code or "import " in code or "print(" in code:
            return "python"
        elif "function " in code or "const " in code or "let " in code:
            return "javascript"
        elif "<html" in code_lower or "<div" in code_lower:
            return "html"
        elif "public class" in code or "private " in code:
            return "java"
        return "javascript"  # Default for executable
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))
    
    def _render_timeline(self, block: ContentBlock) -> str:
        """Render timeline widget from list content."""
        from app.services.plugin_service import plugin_service
        
        plugin = plugin_service.get_plugin("timeline")
        if plugin:
            return plugin.render(block.content, block.id)
        
        # Fallback if plugin not available
        return self._render_list(block.content, block)
    
    def _render_map(self, block: ContentBlock) -> str:
        """Render map widget from location data."""
        from app.services.plugin_service import plugin_service
        
        plugin = plugin_service.get_plugin("map")
        if plugin:
            return plugin.render(block.content, block.id)
        
        # Fallback if plugin not available
        return self._render_block(block)
    
    def _assemble_html(
        self, 
        body_content: str, 
        theme: ThemeType,
        has_charts: bool = False,
        has_code: bool = False,
        has_quiz: bool = False,
        has_executable: bool = False,
        has_timeline: bool = False,
        has_map: bool = False
    ) -> str:
        """Assemble complete HTML document with all required libraries."""
        # External libraries
        libs = []
        if has_charts:
            libs.append('<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>')
        if has_code:
            libs.append('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">')
            libs.append('<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>')
            libs.append('<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>')
            libs.append('<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>')
        if has_map:
            libs.append('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">')
            libs.append('<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>')
        
        # Additional styles for interactive components
        extra_styles = """
        /* Hybrid container for table + chart */
        .hybrid-container { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin: 25px 0; align-items: start; }
        .hybrid-container .table-section { overflow-x: auto; }
        .hybrid-container .chart-section .chart-container { margin: 0; }
        @media (max-width: 900px) { .hybrid-container { grid-template-columns: 1fr; } }
        
        /* Timeline styles */
        .timeline-container { position: relative; padding: 20px 0; margin: 20px 0; }
        .timeline-line { position: absolute; left: 50%; width: 3px; height: 100%; background: linear-gradient(180deg, #4e79a7 0%, #76b7b2 100%); transform: translateX(-50%); border-radius: 3px; }
        .timeline-item { position: relative; margin: 30px 0; width: 45%; }
        .timeline-item.left { left: 0; text-align: right; padding-right: 40px; }
        .timeline-item.right { left: 55%; text-align: left; padding-left: 40px; }
        .timeline-item::before { content: ''; position: absolute; width: 16px; height: 16px; background: #4e79a7; border: 3px solid #fff; border-radius: 50%; top: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
        .timeline-item.left::before { right: -8px; }
        .timeline-item.right::before { left: -8px; }
        .timeline-content { background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 3px 15px rgba(0,0,0,0.1); transition: transform 0.2s, box-shadow 0.2s; }
        .timeline-content:hover { transform: translateY(-3px); box-shadow: 0 5px 20px rgba(0,0,0,0.15); }
        .timeline-date { font-size: 13px; color: #4e79a7; font-weight: 600; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        .timeline-title { font-weight: 700; font-size: 1.1em; margin-bottom: 8px; color: #333; }
        .timeline-desc { font-size: 14px; color: #666; line-height: 1.5; }
        @media (max-width: 768px) {
            .timeline-line { left: 20px; }
            .timeline-item { width: 100%; left: 0 !important; text-align: left !important; padding-left: 50px !important; padding-right: 0 !important; }
            .timeline-item::before { left: 12px !important; right: auto !important; }
        }
        
        /* Map styles */
        .map-container { width: 100%; height: 400px; border-radius: 12px; overflow: hidden; margin: 20px 0; box-shadow: 0 3px 15px rgba(0,0,0,0.1); }
        
        /* Print styles */
        @media print {
            .quiz-check-btn, .run-btn, .copy-btn { display: none; }
            .chart-container { page-break-inside: avoid; }
            .code-executable .code-editor { border: 1px solid #ddd; }
        }
        """
        
        # Prism code highlighting initialization
        prism_init = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    if (typeof Prism !== 'undefined') {
        Prism.highlightAll();
    }
});
</script>
""" if has_code else ""
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="PDF2Web AI Weaver">
    <title>Converted Document</title>
    {chr(10).join(libs)}
    <style>
    {self.theme_styles.get(theme.value, self.theme_styles["light"])}
    {extra_styles}
    </style>
</head>
<body class="theme-{theme.value}">
    <div class="container" role="main">
        {body_content}
    </div>
    {prism_init}
</body>
</html>"""


# Singleton instance
html_generator = HTMLGenerator()
