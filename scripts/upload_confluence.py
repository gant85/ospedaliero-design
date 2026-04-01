"""
Generic script to upload/manage technical documentation on Confluence
Author: agalasso
Date: January 15, 2026

This script provides multiple actions for managing Confluence documentation:
- upload: Upload all markdown files from docs/ folder (default)
- upload-single: Upload a single file
- delete: Delete a specific page
- delete-children: Delete all child pages under a parent

Configuration can be provided via:
1. CLI arguments (highest priority)
2. Environment variables
3. confluence_config.json file (lowest priority)

Examples:
  # Upload all documentation
  python upload_confluence.py

  # Upload single file
  python upload_confluence.py --action upload-single --file docs/ARCHITECTURE.md

  # Delete a page by ID
  python upload_confluence.py --action delete --page-id 123456

  # Delete a page by title
  python upload_confluence.py --action delete --page-title "My Page"

  # Delete all children under a page
  python upload_confluence.py --action delete-children --page-id 123456
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from requests.auth import HTTPBasicAuth
import json
import argparse

# Configure logging with UTF-8 to support Unicode characters on Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('confluence_upload.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure StreamHandler to use UTF-8 on Windows
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler) and hasattr(handler.stream, 'reconfigure'):
        handler.stream.reconfigure(encoding='utf-8')


def load_config(config_file: str = 'confluence_config.json') -> Dict:
    """
    Load configuration from JSON file

    Args:
        config_file: Path to config file (default: confluence_config.json in same directory as script)

    Returns:
        Configuration dictionary (empty if file doesn't exist)
    """
    script_dir = Path(__file__).parent
    config_path = script_dir / config_file

    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"✓ Configuration loaded from {config_file}")
                return config
        except Exception as e:
            logger.warning(f"⚠ Error loading config file {config_file}: {e}")
            return {}
    else:
        logger.info(f"Config file {config_file} not found - using .env or CLI arguments")
        return {}


class ConfluenceUploader:
    """Confluence documentation upload manager"""

    def __init__(self, base_url: str, username: str, api_token: str, space_key: str, project_name: str = "Project", use_plantuml_macro: bool = False):
        """
        Initialize Confluence client

        Args:
            base_url: Confluence base URL (e.g., https://ahi-service.atlassian.net/wiki)
            username: Confluence user email
            api_token: API token generated from Atlassian
            space_key: Confluence space key (e.g., WHOL)
            project_name: Project name for page titles (e.g., "PWP Portal")
            use_plantuml_macro: If True uses PlantUML macro, otherwise external server
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.space_key = space_key
        self.project_name = project_name
        self.use_plantuml_macro = use_plantuml_macro
        self.auth = HTTPBasicAuth(username, api_token)
        self.session = requests.Session()
        self.session.auth = self.auth

        # Map file -> page_id to handle updates
        self.page_map: Dict[str, str] = {}

    def test_connection(self) -> bool:
        """Test Confluence connection"""
        try:
            # Test basic API access
            url = f"{self.base_url}/rest/api/content"
            response = self.session.get(url, params={'limit': 1})
            response.raise_for_status()
            logger.info("✓ Confluence connection successful")

            # Verify space access
            logger.info(f"Verifying access to space: {self.space_key}")
            space_url = f"{self.base_url}/rest/api/space/{self.space_key}"
            space_response = self.session.get(space_url)

            if space_response.status_code == 200:
                space_data = space_response.json()
                logger.info(f"✓ Space found: {space_data.get('name', 'Unknown')} ({self.space_key})")
            elif space_response.status_code == 404:
                logger.error(f"✗ Space not found or not accessible: {self.space_key}")
                logger.error("Please verify the space key is correct and you have access")
                return False
            else:
                logger.warning(f"⚠ Could not verify space (HTTP {space_response.status_code})")

            return True
        except Exception as e:
            logger.error(f"✗ Confluence connection error: {e}")
            return False

    def get_page_by_title(self, title: str, parent_id: Optional[str] = None) -> Optional[Dict]:
        """
        Search for a page by title

        Args:
            title: Page title
            parent_id: Parent page ID (optional)

        Returns:
            Dictionary with page info or None if not found
        """
        try:
            url = f"{self.base_url}/rest/api/content"
            params = {
                'spaceKey': self.space_key,
                'title': title,
                'expand': 'version,ancestors'
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data['results']:
                # If parent_id specified, verify it's the correct parent
                if parent_id:
                    for result in data['results']:
                        ancestors = result.get('ancestors', [])
                        if ancestors and ancestors[-1]['id'] == parent_id:
                            return result
                    return None
                return data['results'][0]
            return None
        except Exception as e:
            logger.error(f"Error searching page '{title}': {e}")
            return None

    def plantuml_to_confluence(self, plantuml_content: str, use_external_server: bool = True) -> str:
        """
        Convert PlantUML file to Confluence format

        Args:
            plantuml_content: PlantUML content
            use_external_server: If True, uses external PlantUML server to generate image
                                 If False, uses Confluence PlantUML macro (requires installation)

        Returns:
            Content in Confluence Storage format
        """
        # Remove @startuml and @enduml if present, preserving any titles
        content = plantuml_content.strip()
        content = re.sub(r'^@startuml.*\n?', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n?@enduml\s*$', '', content, flags=re.MULTILINE)

        if use_external_server:
            # Use public PlantUML server to generate SVG image
            import zlib
            import base64

            # Prepare complete content
            full_content = f"@startuml\n{content}\n@enduml"

            # PlantUML custom encoding (deflate with 6-bit encoding)
            def encode_plantuml(text):
                """Encode text using PlantUML algorithm"""
                # Compress with deflate (level 9)
                compressed = zlib.compress(text.encode('utf-8'), 9)[2:-4]  # Remove zlib header
                # PlantUML uses custom 6-bit base64 encoding
                plantuml_alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'

                encoded = []
                i = 0
                while i < len(compressed):
                    if i + 2 < len(compressed):
                        b1, b2, b3 = compressed[i], compressed[i+1], compressed[i+2]
                        encoded.append(plantuml_alphabet[(b1 >> 2) & 0x3F])
                        encoded.append(plantuml_alphabet[((b1 & 0x3) << 4) | ((b2 >> 4) & 0xF)])
                        encoded.append(plantuml_alphabet[((b2 & 0xF) << 2) | ((b3 >> 6) & 0x3)])
                        encoded.append(plantuml_alphabet[b3 & 0x3F])
                        i += 3
                    elif i + 1 < len(compressed):
                        b1, b2 = compressed[i], compressed[i+1]
                        encoded.append(plantuml_alphabet[(b1 >> 2) & 0x3F])
                        encoded.append(plantuml_alphabet[((b1 & 0x3) << 4) | ((b2 >> 4) & 0xF)])
                        encoded.append(plantuml_alphabet[(b2 & 0xF) << 2])
                        i += 2
                    else:
                        b1 = compressed[i]
                        encoded.append(plantuml_alphabet[(b1 >> 2) & 0x3F])
                        encoded.append(plantuml_alphabet[(b1 & 0x3) << 4])
                        i += 1

                return ''.join(encoded)

            # Codifica il contenuto
            encoded = encode_plantuml(full_content)

            # URL del server PlantUML pubblico (SVG format)
            plantuml_url = f"http://www.plantuml.com/plantuml/svg/{encoded}"

            # Use ac:image macro with data attributes for Confluence's native lightbox
            # The key is to use ac:image without external link wrapper
            confluence_content = f'''<ac:structured-macro ac:name="expand">
<ac:parameter ac:name="title">📊 PlantUML Code</ac:parameter>
<ac:rich-text-body>
<ac:structured-macro ac:name="code">
<ac:parameter ac:name="language">plantuml</ac:parameter>
<ac:plain-text-body><![CDATA[@startuml
{content}
@enduml]]></ac:plain-text-body>
</ac:structured-macro>
</ac:rich-text-body>
</ac:structured-macro>
<p>
<ac:image ac:thumbnail="true" ac:width="800">
<ri:url ri:value="{plantuml_url}" />
</ac:image>
</p>
<p style="font-size: 0.9em; color: #666;">💡 <em>Click diagram to view full size</em></p>'''
        else:
            # Use Confluence PlantUML macro (requires macro installation)
            confluence_content = f'''<ac:structured-macro ac:name="plantuml" ac:schema-version="1">
<ac:plain-text-body><![CDATA[
@startuml
{content}
@enduml
]]></ac:plain-text-body>
</ac:structured-macro>'''

        return confluence_content

    def markdown_to_confluence(self, markdown_content: str, docs_dir: Optional[str] = None) -> str:
        """
        Convert Markdown to Confluence Storage Format

        Args:
            markdown_content: Markdown content
            docs_dir: Path to docs directory (needed to resolve PlantUML diagram references)

        Returns:
            Content in Confluence Storage format
        """
        content = markdown_content

        # STEP 1: Process code blocks FIRST to protect them from other transformations
        code_blocks = []
        def protect_code_block(match):
            language = match.group(1) or 'none'
            code = match.group(2)
            placeholder = f'___CODE_BLOCK_{len(code_blocks)}___'
            code_blocks.append(f'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">{language}</ac:parameter><ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body></ac:structured-macro>')
            return placeholder

        content = re.sub(r'```(\w+)?\n(.*?)```', protect_code_block, content, flags=re.DOTALL)

        # STEP 2: Process inline code (protect from other transformations)
        inline_codes = []
        def protect_inline_code(match):
            code_text = match.group(1)
            placeholder = f'___INLINE_CODE_{len(inline_codes)}___'
            inline_codes.append(f'<code>{code_text}</code>')
            return placeholder

        content = re.sub(r'`([^`]+?)`', protect_inline_code, content)

        # STEP 3: Now process markdown formatting (headings, bold, italic, etc.)
        # Headers (# -> h1, ## -> h2, etc.)
        content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', content, flags=re.MULTILINE)
        content = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', content, flags=re.MULTILINE)

        # Bold (**text** -> <strong>text</strong>)
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)

        # Italic (*text* -> <em>text</em>)
        content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)

        # Links to PlantUML diagrams - embed diagrams directly in page
        # ![Diagram Name](diagrams/06-ordinazione-flow.puml) -> Embedded PlantUML macro
        def replace_plantuml_link(match):
            diagram_display = match.group(1)
            diagram_path = match.group(2)

            # If docs_dir is not provided, cannot resolve diagram - return original
            if not docs_dir:
                logger.warning(f"Cannot resolve PlantUML diagram without docs_dir: {diagram_path}")
                return match.group(0)

            # Build full path to diagram file
            full_path = Path(docs_dir) / diagram_path

            if not full_path.exists():
                logger.warning(f"PlantUML diagram not found: {full_path}")
                return f'<p><em>⚠️ Diagram not found: {diagram_path}</em></p>'

            try:
                # Read PlantUML file content
                with open(full_path, 'r', encoding='utf-8') as f:
                    plantuml_content = f.read()

                # Convert PlantUML to Confluence format (inline embedding)
                confluence_diagram = self.plantuml_to_confluence(plantuml_content, use_external_server=not self.use_plantuml_macro)

                # Add a title above the diagram
                return f'<h4>{diagram_display}</h4>\n{confluence_diagram}'

            except Exception as e:
                logger.error(f"Error reading PlantUML file {full_path}: {e}")
                return f'<p><em>⚠️ Error loading diagram: {diagram_path}</em></p>'

        content = re.sub(r'!\[([^\]]+)\]\((diagrams/[^\)]+\.puml)\)', replace_plantuml_link, content)

        # Links ([text](url) -> <a href="url">text</a>)
        content = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', content)

        # Tables (basic support)
        # | Header | Header |
        # |--------|--------|
        # | Cell   | Cell   |
        def convert_table(table_text):
            lines = [line.strip() for line in table_text.strip().split('\n') if line.strip()]
            if len(lines) < 2:
                return table_text

            # Parse header
            header_cells = [cell.strip() for cell in lines[0].split('|')[1:-1]]

            # Skip separator line (lines[1])

            # Parse rows
            rows = []
            for line in lines[2:]:
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                rows.append(cells)

            # Build Confluence table - direct HTML for storage format
            table_html = '<table><tbody>'

            # Header row
            table_html += '<tr>'
            for cell in header_cells:
                table_html += f'<th>{cell}</th>'
            table_html += '</tr>'

            # Data rows
            for row in rows:
                table_html += '<tr>'
                for cell in row:
                    table_html += f'<td>{cell}</td>'
                table_html += '</tr>'

            table_html += '</tbody></table>'
            return table_html

        # Find and convert tables
        table_pattern = r'(\|.+\|\n\|[-:\s|]+\|\n(?:\|.+\|\n?)+)'
        content = re.sub(table_pattern, lambda m: convert_table(m.group(0)), content, flags=re.MULTILINE)

        # Lists - keep simple and wrap in paragraphs
        # Unordered lists (- item or * item)
        def convert_unordered_list(match):
            list_text = match.group(0)
            items = re.findall(r'^[\-\*]\s+(.+)$', list_text, re.MULTILINE)
            if not items:
                return list_text
            html = '<p><ul>'
            for item in items:
                html += f'<li>{item}</li>'
            html += '</ul></p>'
            return html

        # Ordered lists (1. item, 2. item, etc.)
        def convert_ordered_list(match):
            list_text = match.group(0)
            items = re.findall(r'^\d+\.\s+(.+)$', list_text, re.MULTILINE)
            if not items:
                return list_text
            html = '<p><ol>'
            for item in items:
                html += f'<li>{item}</li>'
            html += '</ol></p>'
            return html

        # Convert lists (process after code blocks and inline code to avoid conflicts)
        content = re.sub(r'((?:^[\-\*]\s+.+$\n?)+)', convert_unordered_list, content, flags=re.MULTILINE)
        content = re.sub(r'((?:^\d+\.\s+.+$\n?)+)', convert_ordered_list, content, flags=re.MULTILINE)

        # Horizontal rule (--- -> <hr/>)
        content = re.sub(r'^---+$', '<hr/>', content, flags=re.MULTILINE)

        # Info/Warning/Note panels
        content = re.sub(r'^\*\*Note:\*\*(.+)$', r'<ac:structured-macro ac:name="info"><ac:rich-text-body>\1</ac:rich-text-body></ac:structured-macro>', content, flags=re.MULTILINE)
        content = re.sub(r'^\*\*Warning:\*\*(.+)$', r'<ac:structured-macro ac:name="warning"><ac:rich-text-body>\1</ac:rich-text-body></ac:structured-macro>', content, flags=re.MULTILINE)

        # Blockquotes (> text)
        content = re.sub(r'^>\s*(.+)$', r'<blockquote>\1</blockquote>', content, flags=re.MULTILINE)

        # Paragraphs (line breaks)
        content = re.sub(r'\n\n', '<p></p>', content)

        # STEP 4: Restore protected inline code
        for i, code_html in enumerate(inline_codes):
            content = content.replace(f'___INLINE_CODE_{i}___', code_html)

        # STEP 5: Restore protected code blocks
        for i, code_block_html in enumerate(code_blocks):
            content = content.replace(f'___CODE_BLOCK_{i}___', code_block_html)

        return content

    def create_page(self, title: str, content: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Crea una nuova pagina Confluence

        Args:
            title: Titolo della pagina
            content: Contenuto in formato Confluence Storage
            parent_id: ID della pagina parent (opzionale)

        Returns:
            ID della pagina creata o None se errore
        """
        try:
            url = f"{self.base_url}/rest/api/content"

            data = {
                'type': 'page',
                'title': title,
                'space': {'key': self.space_key},
                'body': {
                    'storage': {
                        'value': content,
                        'representation': 'storage'
                    }
                }
            }

            if parent_id:
                data['ancestors'] = [{'id': parent_id}]
                logger.debug(f"Creating page with parent ID: {parent_id}")

            logger.debug(f"POST {url}")
            logger.debug(f"Space: {self.space_key}, Title: {title}")

            response = self.session.post(
                url,
                data=json.dumps(data),
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code >= 400:
                logger.error(f"HTTP {response.status_code}: {response.text}")

            response.raise_for_status()

            page_data = response.json()
            page_id = page_data['id']

            logger.info(f"✓ Pagina creata: '{title}' (ID: {page_id})")
            return page_id

        except Exception as e:
            logger.error(f"✗ Errore creazione pagina '{title}': {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return None

    def update_page(self, page_id: str, title: str, content: str, version: int) -> bool:
        """
        Aggiorna una pagina esistente

        Args:
            page_id: ID della pagina
            title: Titolo della pagina
            content: Contenuto in formato Confluence Storage
            version: Versione corrente della pagina

        Returns:
            True se successo, False altrimenti
        """
        try:
            url = f"{self.base_url}/rest/api/content/{page_id}"

            data = {
                'id': page_id,
                'type': 'page',
                'title': title,
                'version': {'number': version + 1},
                'body': {
                    'storage': {
                        'value': content,
                        'representation': 'storage'
                    }
                }
            }

            response = self.session.put(
                url,
                data=json.dumps(data),
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()

            logger.info(f"✓ Pagina aggiornata: '{title}' (v{version} -> v{version + 1})")
            return True

        except Exception as e:
            logger.error(f"✗ Errore aggiornamento pagina '{title}': {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False

    def create_or_update_page(self, title: str, content: str, parent_id: Optional[str] = None, is_plantuml: bool = False, docs_dir: Optional[str] = None) -> Optional[str]:
        """
        Crea o aggiorna una pagina (wrapper intelligente)

        Args:
            title: Titolo della pagina
            content: Contenuto markdown o PlantUML
            parent_id: ID della pagina parent (opzionale)
            is_plantuml: Se True, il contenuto è PlantUML da convertire con macro
            docs_dir: Path to docs directory (needed to resolve PlantUML diagram references in markdown)

        Returns:
            ID della pagina o None se errore
        """
# Convert markdown or PlantUML to Confluence format
        if is_plantuml:
            confluence_content = self.plantuml_to_confluence(content, use_external_server=not self.use_plantuml_macro)
        else:
            confluence_content = self.markdown_to_confluence(content, docs_dir=docs_dir)

        # Search for existing page
        existing_page = self.get_page_by_title(title, parent_id)

        if existing_page:
            # Update existing page
            page_id = existing_page['id']
            version = existing_page['version']['number']

            if self.update_page(page_id, title, confluence_content, version):
                return page_id
            return None
        else:
            # Create new page
            return self.create_page(title, confluence_content, parent_id)

    def generate_page_title(self, filename: str) -> str:
        """
        Genera un titolo leggibile da un filename

        Args:
            filename: Nome del file (es: 01-autenticazione-login.md, README.md)

        Returns:
            Titolo formattato (es: "Project - Autenticazione Login")
        """
        # Caso speciale per README
        if filename.lower() == 'readme.md':
            return f'{self.project_name} - Panoramica'

        # Rimuovi estensione
        name = filename.replace('.md', '')

        # Estrai numero iniziale se presente (es: 01-autenticazione-login -> 01, autenticazione-login)
        number_match = re.match(r'^(\d+)-(.+)', name)
        if number_match:
            number = number_match.group(1)
            name_part = number_match.group(2)
        else:
            number = None
            name_part = name

# Convert dashes to spaces and capitalize each word
        readable_name = name_part.replace('-', ' ')
        readable_name = ' '.join(word.capitalize() for word in readable_name.split())

        # Build title
        if number:
            return f"{self.project_name} - {readable_name}"
        else:
            return f"{self.project_name} - {readable_name}"

    def delete_page(self, page_id: str) -> bool:
        """
        Delete a Confluence page

        Args:
            page_id: ID of the page to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            url = f"{self.base_url}/rest/api/content/{page_id}"
            response = self.session.delete(url)
            response.raise_for_status()
            logger.info(f"✓ Page deleted: {page_id}")
            return True
        except Exception as e:
            logger.error(f"✗ Error deleting page {page_id}: {e}")
            return False

    def get_child_pages(self, parent_id: str) -> List[Dict]:
        """
        Get all child pages of a parent page

        Args:
            parent_id: Parent page ID

        Returns:
            List of child page dictionaries
        """
        try:
            url = f"{self.base_url}/rest/api/content/{parent_id}/child/page"
            params = {'expand': 'version', 'limit': 100}
            all_children = []

            while True:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                all_children.extend(data['results'])

                # Check if there are more pages
                if 'next' in data['_links']:
                    url = self.base_url + data['_links']['next']
                    params = {}  # Params already in the next URL
                else:
                    break

            return all_children
        except Exception as e:
            logger.error(f"✗ Error getting child pages of {parent_id}: {e}")
            return []

    def delete_pages_recursively(self, parent_id: str) -> Tuple[int, int]:
        """
        Delete all child pages recursively under a parent page

        Args:
            parent_id: Parent page ID

        Returns:
            Tuple of (success_count, error_count)
        """
        success_count = 0
        error_count = 0

        # Get all child pages
        children = self.get_child_pages(parent_id)

        for child in children:
            child_id = child['id']
            child_title = child['title']

            # First, recursively delete children of this child
            child_success, child_errors = self.delete_pages_recursively(child_id)
            success_count += child_success
            error_count += child_errors

            # Then delete the child itself
            logger.info(f"Deleting page: {child_title} (ID: {child_id})")
            if self.delete_page(child_id):
                success_count += 1
            else:
                error_count += 1

        return success_count, error_count

    def upload_single_file(self, file_path: str, parent_page_id: Optional[str] = None) -> bool:
        """
        Upload a single markdown or PlantUML file

        Args:
            file_path: Path to the file to upload
            parent_page_id: Parent page ID (optional)

        Returns:
            True if uploaded successfully, False otherwise
        """
        file = Path(file_path)

        if not file.exists():
            logger.error(f"File not found: {file_path}")
            return False

        if not file.suffix.lower() in ['.md', '.puml']:
            logger.error(f"Unsupported file type: {file.suffix}")
            return False

        filename = file.name
        is_plantuml = file.suffix.lower() == '.puml'
        title = self.generate_page_title(filename)

        logger.info(f"Uploading single file: {filename} -> '{title}'")

        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Get docs_dir for proper diagram resolution
            docs_dir = str(file.parent)

            page_id = self.create_or_update_page(
                title=title,
                content=content,
                parent_id=parent_page_id,
                is_plantuml=is_plantuml,
                docs_dir=docs_dir
            )

            if page_id:
                logger.info(f"✓ Successfully uploaded: {filename}")
                return True
            else:
                logger.error(f"✗ Failed to upload: {filename}")
                return False

        except Exception as e:
            logger.error(f"✗ Error uploading {filename}: {e}")
            return False

    def find_parent_for_diagram(self, diagram_filename: str, markdown_files_map: Dict[str, Tuple[str, str]]) -> Optional[Tuple[str, str]]:
        """
        Trova la pagina parent per un diagramma PlantUML basandosi sul prefisso numerico

        Args:
            diagram_filename: Nome file diagramma (es: 01-login-flow.puml)
            markdown_files_map: Mappa {filename: (title, page_id)} dei file markdown già caricati

        Returns:
            Tupla (parent_title, parent_page_id) o None se non trovato
        """
        # Estrai prefisso numerico dal diagramma (es: 01-login-flow.puml -> 01)
        prefix_match = re.match(r'^(\d+)-', diagram_filename)
        if not prefix_match:
            return None

        diagram_prefix = prefix_match.group(1)

        # Cerca file markdown con stesso prefisso
        for md_filename, (title, page_id) in markdown_files_map.items():
            if md_filename.startswith(f"{diagram_prefix}-"):
                return (title, page_id)

        return None

    def upload_documentation(self, docs_dir: str, parent_page_id: Optional[str] = None) -> bool:
        """
        Carica tutta la documentazione dalla directory docs/
        Supporta struttura gerarchica con sottodirectory

        Args:
            docs_dir: Path alla directory docs
            parent_page_id: ID della pagina parent principale

        Returns:
            True se tutto ok, False se errori
        """
        docs_path = Path(docs_dir).resolve()  # Convert to absolute path
        if not docs_path.exists():
            logger.error(f"Directory non trovata: {docs_dir}")
            return False

        error_count = 0
        success_count = 0

        # Mappa {path: (title, page_id)} per tracciare pagine create
        page_registry: Dict[str, Tuple[str, str]] = {}

        logger.info(f"\n{'='*60}")
        logger.info(f"Inizio upload documentazione da: {docs_dir}")
        logger.info(f"Space: {self.space_key}")
        logger.info(f"Parent Page ID: {parent_page_id or 'Root'}")
        logger.info(f"{'='*60}\n")

        # FASE 1: Upload root level pages (README, quick reference, etc)
        logger.info("FASE 1: Upload pagine root level...")
        root_files = sorted([f for f in docs_path.glob('*.md')])

        for md_file in root_files:
            filename = md_file.name
            title = self.generate_page_title(filename)
            logger.info(f"Processing root: {filename} -> '{title}'")

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                page_id = self.create_or_update_page(
                    title=title,
                    content=content,
                    parent_id=parent_page_id,
                    is_plantuml=False,
                    docs_dir=str(docs_path)
                )

                if page_id:
                    page_registry[str(md_file.relative_to(docs_path))] = (title, page_id)
                    success_count += 1
                else:
                    error_count += 1

            except Exception as e:
                logger.error(f"✗ Errore processing {filename}: {e}")
                error_count += 1

        # FASE 2: Upload subdirectories as hierarchical pages
        logger.info(f"\nFASE 2: Upload sottodirectory come pagine gerarchiche...")

        # Get all subdirectories
        subdirs = sorted([d for d in docs_path.iterdir() if d.is_dir() and d.name != 'diagrams'])

        for subdir in subdirs:
            # Create category page (folder becomes a parent page)
            category_name = subdir.name.replace('-', ' ').title()
            category_title = f"{self.project_name} - {category_name}"

            logger.info(f"\nProcessing category: {subdir.name} -> '{category_title}'")

            # Check if category has a README.md file for content
            category_readme = subdir / 'README.md'
            if category_readme.exists():
                logger.info(f"  Using README.md for category content")
                with open(category_readme, 'r', encoding='utf-8') as f:
                    category_content = f.read()
            else:
                # Fallback to generic intro
                category_content = f"<h2>{category_name}</h2><p>This section contains documentation about {category_name.lower()}.</p>"

            category_page_id = self.create_or_update_page(
                title=category_title,
                content=category_content,
                parent_id=parent_page_id,
                is_plantuml=False,
                docs_dir=str(docs_path)
            )

            if not category_page_id:
                logger.error(f"✗ Failed to create category page: {category_title}")
                error_count += 1
                continue

            page_registry[str(subdir.relative_to(docs_path))] = (category_title, category_page_id)
            success_count += 1

            # Upload all markdown files in this subdirectory (skip README.md as it's used for category)
            subdir_files = sorted([f for f in subdir.glob('*.md') if f.name != 'README.md'])
            logger.info(f"  Found {len(subdir_files)} files in {subdir.name}")

            for md_file in subdir_files:
                filename = md_file.name
                title = self.generate_page_title(filename)
                logger.info(f"  Processing: {filename} -> '{title}'")

                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    page_id = self.create_or_update_page(
                        title=title,
                        content=content,
                        parent_id=category_page_id,  # Use category as parent
                        is_plantuml=False,
                        docs_dir=str(docs_path)  # Always use docs root for diagrams
                    )

                    if page_id:
                        page_registry[str(md_file.relative_to(docs_path))] = (title, page_id)
                        success_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    logger.error(f"  ✗ Errore processing {filename}: {e}")
                    error_count += 1

        logger.info(f"\n{'='*60}")
        logger.info(f"Upload completato!")
        logger.info(f"✓ Successi: {success_count}")
        logger.info(f"✗ Errori: {error_count}")
        logger.info(f"{'='*60}\n")

        return error_count == 0


def main():
    """Funzione principale"""
    parser = argparse.ArgumentParser(
        description='Confluence Documentation Manager - Upload, update, or delete pages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload all documentation
  python upload_confluence.py

  # Upload single file
  python upload_confluence.py --action upload-single --file docs/ARCHITECTURE.md

  # Delete page by ID
  python upload_confluence.py --action delete --page-id 514228239

  # Delete page by title
  python upload_confluence.py --action delete --page-title "My Page"

  # Delete all children
  python upload_confluence.py --action delete-children --page-id 514228239

Required Configuration:
  CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN (credentials)
  Optional: CONFLUENCE_BASE_URL, CONFLUENCE_SPACE_KEY, CONFLUENCE_PARENT_ID
        """
    )

    parser.add_argument(
        '--docs-dir',
        help='Directory contenente i file markdown (default: da confluence_config.json)'
    )

    parser.add_argument(
        '--parent-id',
        help='ID della pagina parent su Confluence (default: da confluence_config.json)'
    )

    parser.add_argument(
        '--space-key',
        help='Chiave dello space Confluence (default: da confluence_config.json)'
    )

    parser.add_argument(
        '--project-name',
        help='Nome del progetto per i titoli delle pagine (default: da confluence_config.json)'
    )

    parser.add_argument(
        '--base-url',
        help='URL base Confluence (default: da confluence_config.json)'
    )

    parser.add_argument(
        '--use-plantuml-macro',
        action='store_true',
        help='Usa macro PlantUML di Confluence (richiede installazione). Default: usa server PlantUML esterno'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test senza caricare realmente'
    )

    parser.add_argument(
        '--env-file',
        help='Path al file .env (default: scripts/.env)'
    )

    # New action-based arguments
    parser.add_argument(
        '--action',
        choices=['upload', 'upload-single', 'delete', 'delete-children'],
        default='upload',
        help='Action to perform: upload (all docs), upload-single (one file), delete (one page), delete-children (all under a page)'
    )

    parser.add_argument(
        '--file',
        help='Path to single file for upload-single action (e.g., docs/ARCHITECTURE.md)'
    )

    parser.add_argument(
        '--page-id',
        help='Page ID for delete/delete-children actions'
    )

    parser.add_argument(
        '--page-title',
        help='Page title to search and delete (alternative to --page-id)'
    )

    args = parser.parse_args()

    # Load configuration from external file
    config = load_config()

    # Leggi configurazione da variabili ambiente o .env
    username = os.getenv('CONFLUENCE_USERNAME')
    api_token = os.getenv('CONFLUENCE_API_TOKEN')
    base_url = os.getenv('CONFLUENCE_BASE_URL')
    space_key = os.getenv('CONFLUENCE_SPACE_KEY')
    parent_id = os.getenv('CONFLUENCE_PARENT_ID')

    # Determina il path del file .env
    if args.env_file:
        env_file = Path(args.env_file)
    else:
        # Default: cerca .env nella directory scripts/
        script_dir = Path(__file__).parent
        env_file = script_dir / '.env'

    # Se non trovate nelle variabili ambiente, prova a leggere da .env file
    if env_file.exists():
        logger.info(f"Loading environment from: {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key == 'CONFLUENCE_USERNAME' and not username:
                            username = value
                        elif key == 'CONFLUENCE_API_TOKEN' and not api_token:
                            api_token = value
                        elif key == 'CONFLUENCE_BASE_URL' and not base_url:
                            base_url = value
                        elif key == 'CONFLUENCE_SPACE_KEY' and not space_key:
                            space_key = value
                        elif key == 'CONFLUENCE_PARENT_ID' and not parent_id:
                            parent_id = value
    else:
        logger.info(f".env file not found at: {env_file}")

    # Gli argomenti CLI hanno priorità sulle variabili d'ambiente
    # Applica PRIMA della validazione per permettere override completo
    if args.base_url:
        base_url = args.base_url
    if args.space_key:
        space_key = args.space_key
    if args.parent_id:
        parent_id = args.parent_id

    # Applica valori dal file di configurazione se ancora mancanti
    if not base_url:
        base_url = config.get('default_base_url')
    if not space_key:
        space_key = config.get('default_space_key')
    if not parent_id:
        parent_id = config.get('default_parent_id')

    # Usa project_name dal config se non specificato da CLI
    if not args.project_name:
        args.project_name = config.get('project_name', 'Project')

    # Usa docs_dir dal config se non specificato da CLI
    if not args.docs_dir:
        args.docs_dir = config.get('docs_dir', 'docs')

    # Validazione configurazione completa
    # TUTTE le variabili sono obbligatorie
    missing_vars = []
    if not username:
        missing_vars.append('CONFLUENCE_USERNAME')
    if not api_token:
        missing_vars.append('CONFLUENCE_API_TOKEN')
    if not base_url:
        missing_vars.append('CONFLUENCE_BASE_URL')
    if not space_key:
        missing_vars.append('CONFLUENCE_SPACE_KEY')
    if not parent_id:
        missing_vars.append('CONFLUENCE_PARENT_ID')

    if missing_vars:
        logger.error("Configurazione Confluence incompleta!")
        logger.error(f"Variabili obbligatorie mancanti: {', '.join(missing_vars)}")
        logger.error("")
        logger.error("Imposta le seguenti variabili nel file .env o scripts/confluence_config.json:")
        logger.error("  CONFLUENCE_USERNAME=your-email@alliance-healthcare.it")
        logger.error("  CONFLUENCE_API_TOKEN=your-api-token")
        logger.error("  CONFLUENCE_BASE_URL=https://ahi-service.atlassian.net/wiki")
        logger.error("  CONFLUENCE_SPACE_KEY=YOUR_SPACE_KEY")
        logger.error("  CONFLUENCE_PARENT_ID=YOUR_PARENT_PAGE_ID")
        logger.error("")
        logger.error("Oppure usa --base-url, --space-key, --parent-id da CLI")
        return 1

    logger.info(f"=== {args.project_name} - Confluence Manager ===")
    logger.info(f"Action: {args.action}")
    logger.info(f"Username: {username}")
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Space: {space_key}")
    logger.info(f"Parent ID: {parent_id}")
    logger.info(f"Project: {args.project_name}")
    logger.info(f"Docs dir: {args.docs_dir}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(f"Target: {base_url}/spaces/{space_key}/pages/{parent_id}")
    logger.info("")

    if args.dry_run:
        logger.info("DRY RUN MODE - Nessun caricamento reale")
        # TODO: implementare dry run
        return 0

    # Crea uploader
    uploader = ConfluenceUploader(
        base_url=base_url,
        username=username,
        api_token=api_token,
        space_key=space_key,
        project_name=args.project_name,
        use_plantuml_macro=args.use_plantuml_macro
    )

    # Test connessione
    if not uploader.test_connection():
        logger.error("Impossibile connettersi a Confluence")
        return 1

    # Execute action based on --action parameter
    if args.action == 'upload':
        # Upload all documentation
        success = uploader.upload_documentation(
            docs_dir=args.docs_dir,
            parent_page_id=parent_id
        )
        return 0 if success else 1

    elif args.action == 'upload-single':
        # Upload single file
        if not args.file:
            logger.error("--file required for upload-single action")
            return 1

        success = uploader.upload_single_file(
            file_path=args.file,
            parent_page_id=parent_id
        )
        return 0 if success else 1

    elif args.action == 'delete':
        # Delete single page
        page_id_to_delete = args.page_id

        # If page title provided instead of ID, search for it
        if not page_id_to_delete and args.page_title:
            logger.info(f"Searching for page: {args.page_title}")
            page = uploader.get_page_by_title(args.page_title)
            if page:
                page_id_to_delete = page['id']
                logger.info(f"Found page ID: {page_id_to_delete}")
            else:
                logger.error(f"Page not found: {args.page_title}")
                return 1

        if not page_id_to_delete:
            logger.error("--page-id or --page-title required for delete action")
            return 1

        logger.info(f"Deleting page ID: {page_id_to_delete}")
        success = uploader.delete_page(page_id_to_delete)
        return 0 if success else 1

    elif args.action == 'delete-children':
        # Delete all children pages
        page_id_parent = args.page_id or parent_id

        logger.info(f"Deleting all children of page ID: {page_id_parent}")
        logger.warning("This will delete ALL child pages recursively!")

        # Ask for confirmation (skip in CI/CD)
        if not os.getenv('CI'):
            response = input("Are you sure? Type 'yes' to continue: ")
            if response.lower() != 'yes':
                logger.info("Operation cancelled")
                return 0

        success_count, error_count = uploader.delete_pages_recursively(page_id_parent)
        logger.info(f"\nDeletion complete:")
        logger.info(f"  Deleted: {success_count}")
        logger.info(f"  Errors: {error_count}")
        return 0 if error_count == 0 else 1

    else:
        logger.error(f"Unknown action: {args.action}")
        return 1


if __name__ == '__main__':
    exit(main())
