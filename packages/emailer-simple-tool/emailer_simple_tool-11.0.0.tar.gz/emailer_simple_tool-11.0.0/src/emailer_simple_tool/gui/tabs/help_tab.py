"""
Help Tab - Integrated documentation and user guide
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import pkgutil

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QTextBrowser, QTreeWidget, QTreeWidgetItem,
    QSplitter, QGroupBox, QFrame, QScrollArea, QToolBar,
    QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QCoreApplication, QTimer
from PySide6.QtGui import QFont, QIcon, QAction, QPixmap


class HelpTab(QWidget):
    """Help and documentation tab with integrated user guide"""
    
    def __init__(self, campaign_manager):
        super().__init__()
        self.campaign_manager = campaign_manager
        
        # Help content structure
        self.help_sections = {
            "quick_start": {
                "en": "🚀 Quick Start (5 minutes)",
                "fr": "🚀 Démarrage Rapide (5 minutes)",
                "icon": "🚀"
            },
            "campaign_setup": {
                "en": "📁 Campaign Setup",
                "fr": "📁 Configuration de Campagne",
                "icon": "📁"
            },
            "smtp_config": {
                "en": "📧 Email Configuration",
                "fr": "📧 Configuration Email",
                "icon": "📧"
            },
            "picture_generator": {
                "en": "🖼️ Picture Generator",
                "fr": "🖼️ Générateur d'Images",
                "icon": "🖼️"
            },
            "email_sending": {
                "en": "🚀 Email Sending",
                "fr": "🚀 Envoi d'Emails",
                "icon": "🚀"
            },
            "troubleshooting": {
                "en": "🔧 Troubleshooting",
                "fr": "🔧 Dépannage",
                "icon": "🔧"
            },
            "faq": {
                "en": "❓ FAQ",
                "fr": "❓ FAQ",
                "icon": "❓"
            },
            "about": {
                "en": "ℹ️ About",
                "fr": "ℹ️ À Propos",
                "icon": "ℹ️"
            }
        }
        
        # Content cache for performance
        self.content_cache = {}
        
        # Current language
        self.current_language = "en"
        
        self.init_ui()
        
        # Load initial content
        QTimer.singleShot(100, self.load_initial_content)
    
    def init_ui(self):
        """Initialize help tab UI"""
        layout = QVBoxLayout()
        
        # Create main splitter for navigation and content
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Navigation
        nav_panel = self.create_navigation_panel()
        
        # Right panel - Content display
        content_panel = self.create_content_panel()
        
        # Add panels to splitter
        main_splitter.addWidget(nav_panel)
        main_splitter.addWidget(content_panel)
        
        # Set initial sizes (25% navigation, 75% content)
        main_splitter.setSizes([300, 900])
        main_splitter.setStretchFactor(0, 0)  # Navigation panel doesn't stretch
        main_splitter.setStretchFactor(1, 1)  # Content panel stretches
        
        layout.addWidget(main_splitter)
        self.setLayout(layout)
    
    def create_navigation_panel(self) -> QWidget:
        """Create the left navigation panel"""
        panel = QWidget()
        panel.setMaximumWidth(400)
        panel.setMinimumWidth(250)
        
        layout = QVBoxLayout()
        
        # Search section
        search_group = QGroupBox(self.tr("🔍 Search Help"))
        search_layout = QVBoxLayout()
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(self.tr("Search documentation..."))
        self.search_box.textChanged.connect(self.perform_search)
        
        search_layout.addWidget(self.search_box)
        search_group.setLayout(search_layout)
        
        # Navigation tree
        nav_group = QGroupBox(self.tr("📚 Help Topics"))
        nav_layout = QVBoxLayout()
        
        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.itemClicked.connect(self.on_section_selected)
        self.populate_navigation_tree()
        
        nav_layout.addWidget(self.nav_tree)
        nav_group.setLayout(nav_layout)
        
        # Quick actions
        actions_group = QGroupBox(self.tr("⚡ Quick Actions"))
        actions_layout = QVBoxLayout()
        
        self.contextual_help_btn = QPushButton(self.tr("📍 Help for Current Tab"))
        self.contextual_help_btn.clicked.connect(self.show_contextual_help)
        
        self.print_btn = QPushButton(self.tr("🖨️ Print Current Page"))
        self.print_btn.clicked.connect(self.print_current_page)
        
        actions_layout.addWidget(self.contextual_help_btn)
        actions_layout.addWidget(self.print_btn)
        actions_group.setLayout(actions_layout)
        
        # Add all groups to panel
        layout.addWidget(search_group)
        layout.addWidget(nav_group)
        layout.addWidget(actions_group)
        layout.addStretch()  # Push everything to top
        
        panel.setLayout(layout)
        return panel
    
    def create_content_panel(self) -> QWidget:
        """Create the right content display panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Content toolbar
        toolbar = self.create_content_toolbar()
        layout.addWidget(toolbar)
        
        # Main content area
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)
        self.setup_content_styling()
        
        layout.addWidget(self.content_browser)
        
        # Status bar for content
        self.content_status = QLabel(self.tr("Ready - Select a help topic to get started"))
        self.content_status.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(self.content_status)
        
        panel.setLayout(layout)
        return panel
    
    def create_content_toolbar(self) -> QWidget:
        """Create toolbar for content area"""
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Back/Forward navigation
        self.back_btn = QPushButton(self.tr("← Back"))
        self.back_btn.setEnabled(False)
        self.back_btn.clicked.connect(self.go_back)
        
        self.forward_btn = QPushButton(self.tr("Forward →"))
        self.forward_btn.setEnabled(False)
        self.forward_btn.clicked.connect(self.go_forward)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        
        # Font size controls
        self.font_smaller_btn = QPushButton(self.tr("A-"))
        self.font_smaller_btn.setToolTip(self.tr("Decrease font size"))
        self.font_smaller_btn.clicked.connect(self.decrease_font_size)
        
        self.font_larger_btn = QPushButton(self.tr("A+"))
        self.font_larger_btn.setToolTip(self.tr("Increase font size"))
        self.font_larger_btn.clicked.connect(self.increase_font_size)
        
        # Add widgets to toolbar
        toolbar_layout.addWidget(self.back_btn)
        toolbar_layout.addWidget(self.forward_btn)
        toolbar_layout.addWidget(separator)
        toolbar_layout.addWidget(self.font_smaller_btn)
        toolbar_layout.addWidget(self.font_larger_btn)
        toolbar_layout.addStretch()  # Push everything to left
        
        toolbar_widget.setLayout(toolbar_layout)
        return toolbar_widget
    
    def populate_navigation_tree(self):
        """Populate the navigation tree with help sections"""
        self.nav_tree.clear()
        
        for section_id, section_info in self.help_sections.items():
            item = QTreeWidgetItem()
            
            # Get localized title
            title = section_info.get(self.current_language, section_info["en"])
            item.setText(0, title)
            item.setData(0, Qt.UserRole, section_id)
            
            self.nav_tree.addTopLevelItem(item)
        
        # Expand all items
        self.nav_tree.expandAll()
    
    def setup_content_styling(self):
        """Set up styling for the content browser"""
        # Set font
        font = QFont()
        font.setFamily("system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif")
        font.setPointSize(11)
        self.content_browser.setFont(font)
        
        # Set stylesheet for better appearance
        self.content_browser.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 15px;
                line-height: 1.6;
            }
        """)
    
    def load_initial_content(self):
        """Load initial welcome content"""
        welcome_content = self.get_welcome_content()
        self.content_browser.setHtml(welcome_content)
        self.content_status.setText(self.tr("Welcome to Emailer Simple Tool Help"))
    
    def get_welcome_content(self) -> str:
        """Generate welcome content for the help system"""
        if self.current_language == "fr":
            return """
            <h1>🎉 Bienvenue dans l'Aide d'Emailer Simple Tool</h1>
            
            <p>Cette section d'aide intégrée vous fournit un accès immédiat à toute la documentation 
            dont vous avez besoin pour utiliser efficacement Emailer Simple Tool.</p>
            
            <h2>🚀 Pour Commencer</h2>
            <ul>
                <li><strong>Démarrage Rapide</strong> - Configuration en 5 minutes</li>
                <li><strong>Configuration de Campagne</strong> - Créer votre première campagne</li>
                <li><strong>Configuration Email</strong> - Paramétrer votre serveur SMTP</li>
            </ul>
            
            <h2>📚 Navigation</h2>
            <p>Utilisez le panneau de navigation à gauche pour parcourir les différentes sections d'aide. 
            Vous pouvez également utiliser la fonction de recherche pour trouver rapidement des informations spécifiques.</p>
            
            <h2>💡 Conseils</h2>
            <ul>
                <li>Cliquez sur "Aide pour l'Onglet Actuel" pour obtenir de l'aide contextuelle</li>
                <li>Utilisez Ctrl+F pour rechercher dans le contenu actuel</li>
                <li>Ajustez la taille de la police avec les boutons A- et A+</li>
            </ul>
            
            <p><em>Sélectionnez un sujet dans le panneau de navigation pour commencer!</em></p>
            """
        else:
            return """
            <h1>🎉 Welcome to Emailer Simple Tool Help</h1>
            
            <p>This integrated help system provides you with immediate access to all the documentation 
            you need to use Emailer Simple Tool effectively.</p>
            
            <h2>🚀 Getting Started</h2>
            <ul>
                <li><strong>Quick Start</strong> - Get up and running in 5 minutes</li>
                <li><strong>Campaign Setup</strong> - Create your first email campaign</li>
                <li><strong>Email Configuration</strong> - Set up your SMTP server</li>
            </ul>
            
            <h2>📚 Navigation</h2>
            <p>Use the navigation panel on the left to browse through different help sections. 
            You can also use the search function to quickly find specific information.</p>
            
            <h2>💡 Tips</h2>
            <ul>
                <li>Click "Help for Current Tab" to get contextual help</li>
                <li>Use Ctrl+F to search within the current content</li>
                <li>Adjust font size with the A- and A+ buttons</li>
            </ul>
            
            <p><em>Select a topic from the navigation panel to get started!</em></p>
            """
    
    def on_section_selected(self, item: QTreeWidgetItem, column: int):
        """Handle selection of a help section"""
        section_id = item.data(0, Qt.UserRole)
        if section_id:
            self.load_section_content(section_id)
    
    def load_section_content(self, section_id: str):
        """Load content for a specific help section"""
        try:
            content = self.get_section_content(section_id)
            if content:
                self.content_browser.setHtml(content)
                section_title = self.help_sections[section_id].get(self.current_language, 
                                                                 self.help_sections[section_id]["en"])
                self.content_status.setText(self.tr(f"Viewing: {section_title}"))
            else:
                self.show_content_not_available(section_id)
        except Exception as e:
            self.show_error_content(section_id, str(e))
    
    def get_section_content(self, section_id: str) -> str:
        """Get content for a help section"""
        # Check cache first
        cache_key = f"{section_id}_{self.current_language}"
        if cache_key in self.content_cache:
            return self.content_cache[cache_key]
        
        # Try to load from resources
        content = self.load_content_from_resources(section_id, self.current_language)
        
        # If French content not available, try English
        if not content and self.current_language == "fr":
            content = self.load_content_from_resources(section_id, "en")
        
        # If still no content, generate placeholder
        if not content:
            content = self.generate_placeholder_content(section_id)
        
        # Process and cache content
        processed_content = self.process_content(content, section_id)
        self.content_cache[cache_key] = processed_content
        
        return processed_content
    
    def load_content_from_resources(self, section_id: str, language: str) -> Optional[str]:
        """Load content from packaged resources"""
        try:
            resource_path = f"gui/help/{language}/{section_id}.md"
            content_bytes = pkgutil.get_data("emailer_simple_tool", resource_path)
            if content_bytes:
                return content_bytes.decode('utf-8')
        except Exception:
            pass
        return None
    
    def generate_placeholder_content(self, section_id: str) -> str:
        """Generate placeholder content for missing sections"""
        section_title = self.help_sections[section_id].get(self.current_language, 
                                                          self.help_sections[section_id]["en"])
        
        if self.current_language == "fr":
            return f"""
            <h1>{section_title}</h1>
            <p><em>Cette section de documentation est en cours de développement.</em></p>
            <p>En attendant, vous pouvez:</p>
            <ul>
                <li>Consulter la section "Démarrage Rapide" pour les bases</li>
                <li>Utiliser la fonction de recherche pour trouver des informations spécifiques</li>
                <li>Consulter la FAQ pour les questions courantes</li>
            </ul>
            """
        else:
            return f"""
            <h1>{section_title}</h1>
            <p><em>This documentation section is under development.</em></p>
            <p>In the meantime, you can:</p>
            <ul>
                <li>Check the "Quick Start" section for basics</li>
                <li>Use the search function to find specific information</li>
                <li>Browse the FAQ for common questions</li>
            </ul>
            """
    
    def process_content(self, content: str, section_id: str) -> str:
        """Process markdown content to HTML"""
        # For now, simple markdown-like processing
        # In a full implementation, you'd use a proper markdown library
        
        # Convert headers
        content = content.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
        content = content.replace('## ', '<h2>').replace('\n', '</h2>\n')
        content = content.replace('### ', '<h3>').replace('\n', '</h3>\n')
        
        # Convert paragraphs
        lines = content.split('\n')
        processed_lines = []
        in_paragraph = False
        
        for line in lines:
            line = line.strip()
            if not line:
                if in_paragraph:
                    processed_lines.append('</p>')
                    in_paragraph = False
                processed_lines.append('')
            elif line.startswith('<h') or line.startswith('<ul') or line.startswith('<li'):
                if in_paragraph:
                    processed_lines.append('</p>')
                    in_paragraph = False
                processed_lines.append(line)
            else:
                if not in_paragraph:
                    processed_lines.append('<p>')
                    in_paragraph = True
                processed_lines.append(line)
        
        if in_paragraph:
            processed_lines.append('</p>')
        
        return '\n'.join(processed_lines)
    
    def show_content_not_available(self, section_id: str):
        """Show content not available message"""
        section_title = self.help_sections[section_id].get(self.current_language, 
                                                          self.help_sections[section_id]["en"])
        
        if self.current_language == "fr":
            content = f"""
            <h1>Contenu Non Disponible</h1>
            <p>Le contenu pour "{section_title}" n'est pas encore disponible.</p>
            <p>Cette section sera ajoutée dans une future mise à jour.</p>
            """
        else:
            content = f"""
            <h1>Content Not Available</h1>
            <p>Content for "{section_title}" is not yet available.</p>
            <p>This section will be added in a future update.</p>
            """
        
        self.content_browser.setHtml(content)
        self.content_status.setText(self.tr("Content not available"))
    
    def show_error_content(self, section_id: str, error: str):
        """Show error message when content loading fails"""
        if self.current_language == "fr":
            content = f"""
            <h1>Erreur de Chargement</h1>
            <p>Impossible de charger le contenu pour cette section.</p>
            <p><strong>Erreur:</strong> {error}</p>
            """
        else:
            content = f"""
            <h1>Loading Error</h1>
            <p>Failed to load content for this section.</p>
            <p><strong>Error:</strong> {error}</p>
            """
        
        self.content_browser.setHtml(content)
        self.content_status.setText(self.tr("Error loading content"))
    
    def perform_search(self, query: str):
        """Perform search across help content"""
        if len(query) < 2:
            return
        
        # Simple search implementation
        # In a full implementation, you'd have a proper search index
        results = []
        
        for section_id, section_info in self.help_sections.items():
            section_title = section_info.get(self.current_language, section_info["en"])
            if query.lower() in section_title.lower():
                results.append((section_id, section_title))
        
        # Update navigation tree to show search results
        self.update_navigation_for_search(results, query)
    
    def update_navigation_for_search(self, results: List[tuple], query: str):
        """Update navigation tree to show search results"""
        if not query or len(query) < 2:
            self.populate_navigation_tree()
            return
        
        self.nav_tree.clear()
        
        if results:
            search_item = QTreeWidgetItem()
            search_item.setText(0, self.tr(f"🔍 Search Results for '{query}'"))
            search_item.setExpanded(True)
            self.nav_tree.addTopLevelItem(search_item)
            
            for section_id, section_title in results:
                result_item = QTreeWidgetItem(search_item)
                result_item.setText(0, section_title)
                result_item.setData(0, Qt.UserRole, section_id)
        else:
            no_results_item = QTreeWidgetItem()
            no_results_item.setText(0, self.tr(f"🔍 No results for '{query}'"))
            self.nav_tree.addTopLevelItem(no_results_item)
    
    def show_contextual_help(self):
        """Show help relevant to the current active tab"""
        # Get the current tab from the main window
        try:
            main_window = self.window()
            if hasattr(main_window, 'tabs'):
                current_index = main_window.tabs.currentIndex()
                current_tab = main_window.tabs.widget(current_index)
                
                # Map tab types to help sections
                tab_help_mapping = {
                    'CampaignTab': 'campaign_setup',
                    'SMTPTab': 'smtp_config',
                    'PictureTab': 'picture_generator',
                    'SendTab': 'email_sending'
                }
                
                tab_class_name = current_tab.__class__.__name__
                if tab_class_name in tab_help_mapping:
                    help_section = tab_help_mapping[tab_class_name]
                    self.load_section_content(help_section)
                    
                    # Select the item in navigation tree
                    for i in range(self.nav_tree.topLevelItemCount()):
                        item = self.nav_tree.topLevelItem(i)
                        if item.data(0, Qt.UserRole) == help_section:
                            self.nav_tree.setCurrentItem(item)
                            break
                else:
                    self.load_section_content('quick_start')
        except Exception:
            # Fallback to quick start
            self.load_section_content('quick_start')
    
    def print_current_page(self):
        """Print the current help page"""
        # Simple implementation - in a full version you'd use QPrinter
        QMessageBox.information(
            self,
            self.tr("Print"),
            self.tr("Print functionality will be implemented in a future version.\n"
                   "For now, you can use Ctrl+A to select all text and Ctrl+C to copy it.")
        )
    
    def go_back(self):
        """Navigate back in help history"""
        # Placeholder for navigation history
        pass
    
    def go_forward(self):
        """Navigate forward in help history"""
        # Placeholder for navigation history
        pass
    
    def increase_font_size(self):
        """Increase content font size"""
        font = self.content_browser.font()
        current_size = font.pointSize()
        if current_size < 20:  # Maximum size limit
            font.setPointSize(current_size + 1)
            self.content_browser.setFont(font)
    
    def decrease_font_size(self):
        """Decrease content font size"""
        font = self.content_browser.font()
        current_size = font.pointSize()
        if current_size > 8:  # Minimum size limit
            font.setPointSize(current_size - 1)
            self.content_browser.setFont(font)
    
    def set_language(self, language: str):
        """Set the current language and update content"""
        if language != self.current_language:
            self.current_language = language
            self.retranslate_ui()
            self.populate_navigation_tree()
            # Reload current content in new language
            self.load_initial_content()
    
    def retranslate_ui(self):
        """Update UI text when language changes"""
        # This will be called by the main window when language changes
        # Update all translatable strings
        pass
