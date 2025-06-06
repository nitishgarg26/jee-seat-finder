# pdf_generator.py - Complete PDF generation with emoji support and enhanced statistics

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
import datetime
import pandas as pd
import io
import requests
import os


class EmojiImageManager:
    """Manages emoji image downloads and embedding"""
    
    def __init__(self, image_size=16):
        self.image_size = image_size
        self.emoji_cache = {}
        
        # Map emojis to their Unicode codepoints
        self.emoji_map = {
            '🎓': '1f393',
            '📊': '1f4ca',
            '🏆': '1f3c6',
            '🏫': '1f3eb',
            '📚': '1f4da',
            '💺': '1f4ba',
            '🎟️': '1f39f',
            '👤': '1f464',
            '📝': '1f4dd',
            '📈': '1f4c8',
            '🔍': '1f50d',
            '📄': '1f4c4',
            '⭐': '2b50',
            '✅': '2705',
            '❌': '274c',
            '⚠️': '26a0'
        }
        
        # Working CDN alternatives (in order of preference)
        self.cdn_urls = [
            "https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{}.png",
            "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/{}.png",
            "https://unpkg.com/twemoji@14.0.2/assets/72x72/{}.png"
        ]
    
    def download_emoji_image(self, emoji_char):
        """Download emoji PNG from working CDNs"""
        if emoji_char in self.emoji_cache:
            return self.emoji_cache[emoji_char]
        
        if emoji_char not in self.emoji_map:
            return None
        
        codepoint = self.emoji_map[emoji_char]
        filename = f"emoji_{codepoint}.png"
        
        if not os.path.exists(filename):
            # Try multiple CDNs until one works
            for cdn_template in self.cdn_urls:
                try:
                    url = cdn_template.format(codepoint)
                    print(f"🔄 Trying to download {emoji_char} from {url}")
                    
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        print(f"✅ Downloaded emoji: {emoji_char} from {url}")
                        break
                    else:
                        print(f"❌ Failed with status {response.status_code}: {url}")
                        
                except Exception as e:
                    print(f"❌ Error with {url}: {e}")
                    continue
            else:
                print(f"❌ Failed to download {emoji_char} from all CDNs")
                return None
        
        self.emoji_cache[emoji_char] = filename
        return filename
    
    def create_emoji_image(self, emoji_char, width=None, height=None):
        """Create ReportLab Image object for emoji"""
        image_path = self.download_emoji_image(emoji_char)
        if not image_path:
            return None
        
        try:
            width = width or self.image_size
            height = height or self.image_size
            return Image(image_path, width=width, height=height)
        except Exception as e:
            print(f"❌ Error creating image for {emoji_char}: {e}")
            return None
    
    def create_emoji_or_text(self, emoji_char, fallback_text, width=None, height=None):
        """Create emoji image or fallback to text"""
        emoji_image = self.create_emoji_image(emoji_char, width, height)
        if emoji_image:
            return emoji_image
        else:
            return fallback_text
    
    def download_all_emojis(self):
        """Pre-download all emojis used in the app"""
        print("📥 Pre-downloading emoji images from working CDNs...")
        success_count = 0
        for emoji_char in self.emoji_map.keys():
            if self.download_emoji_image(emoji_char):
                success_count += 1
        print(f"✅ Downloaded {success_count}/{len(self.emoji_map)} emoji images successfully!")
        return success_count > 0


def generate_enhanced_statistics(df, story, styles, emoji_manager=None):
    """Generate enhanced statistics with text wrapping for institute names"""
    
    if len(df) == 0:
        return
    
    # Statistics title
    if emoji_manager:
        stats_emoji = emoji_manager.create_emoji_or_text('📈', '📈', 16, 16)
        if isinstance(stats_emoji, str):
            stats_title = Paragraph(f"{stats_emoji} Summary Statistics", styles['Heading2'])
            story.append(stats_title)
        else:
            stats_table_data = [[stats_emoji, "Summary Statistics"]]
            stats_table = Table(stats_table_data, colWidths=[0.3*inch, 4*inch])
            stats_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (1, 0), 16),
                ('TEXTCOLOR', (1, 0), (1, 0), HexColor('#667eea')),
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 10))
    else:
        stats_title = Paragraph("📈 Summary Statistics", styles['Heading2'])
        story.append(stats_title)
    
    story.append(Spacer(1, 10))
    
    # Enhanced Institute breakdown with text wrapping
    institute_counts = df['institute'].value_counts()
    if len(institute_counts) > 0:
        # Create style for table cells with wrapping
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,  # Line spacing
            alignment=0  # Left alignment
        )
        
        # Header style
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            fontName='Helvetica-Bold',
            textColor=white,
            alignment=1  # Center alignment
        )
        
        # Create institute statistics table with Paragraph objects
        institute_data = []
        
        # Header row
        institute_data.append([
            Paragraph("🏫 Institute Analysis", header_style),
            Paragraph("# Options", header_style),
            Paragraph("% Share", header_style),
            Paragraph("Avg Rank", header_style)
        ])
        
        for institute, count in institute_counts.head(8).items():
            percentage = (count / len(df)) * 100
            
            # Calculate average rank for this institute
            institute_df = df[df['institute'] == institute]
            avg_institute_rank = institute_df['closing_rank'].mean()
            
            # Use Paragraph for institute name to enable wrapping
            institute_data.append([
                Paragraph(str(institute), cell_style),  # NO TRUNCATION - will wrap
                Paragraph(str(count), cell_style),
                Paragraph(f'{percentage:.1f}%', cell_style),
                Paragraph(f'{int(avg_institute_rank):,}', cell_style)
            ])
        
        # FULL PAGE WIDTH with text wrapping
        institute_table = Table(institute_data, colWidths=[4.5*inch, 1.0*inch, 1.0*inch, 1.0*inch])
        institute_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Left align institute names
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Top align for wrapped text
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#d4edda')),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#c3e6cb')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#d4edda'), HexColor('#c3e6cb')])
        ]))
        story.append(institute_table)
        story.append(Spacer(1, 20))


def generate_shortlist_pdf(df, username):
    """
    Generate PDF with emoji images from working CDNs and enhanced statistics
    
    Args:
        df (pandas.DataFrame): Shortlist data
        username (str): User's name for the report
    
    Returns:
        bytes: PDF file as bytes
    """
    try:
        # Initialize emoji manager
        emoji_manager = EmojiImageManager(image_size=12)
        has_emojis = emoji_manager.download_all_emojis()
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(8.5*inch, 11*inch),
            rightMargin=50,
            leftMargin=50,
            topMargin=72,
            bottomMargin=50
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            textColor=HexColor('#667eea'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            textColor=HexColor('#333333'),
            alignment=TA_CENTER
        )
        
        # Title with emoji or fallback
        title_content = emoji_manager.create_emoji_or_text('🎓', '★', 24, 24)
        if isinstance(title_content, str):
            # Fallback to text
            title = Paragraph(f"{title_content} JEE Seat Finder - My Shortlist", title_style)
            story.append(title)
            story.append(Spacer(1, 20))
        else:
            # Use emoji image
            title_table_data = [[title_content, "JEE Seat Finder - My Shortlist"]]
            title_table = Table(title_table_data, colWidths=[0.5*inch, 6*inch])
            title_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (1, 0), 18),
                ('TEXTCOLOR', (1, 0), (1, 0), HexColor('#667eea')),
            ]))
            story.append(title_table)
            story.append(Spacer(1, 20))
        
        # User info
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        user_info = Paragraph(f"<b>Student:</b> {username} | <b>Generated on:</b> {current_date}", subtitle_style)
        story.append(user_info)
        story.append(Spacer(1, 20))
        
        # Summary with emoji or fallback
        summary_emoji = emoji_manager.create_emoji_or_text('📊', '■', 16, 16)
        if isinstance(summary_emoji, str):
            summary = Paragraph(f"{summary_emoji} <b>Total Options in Shortlist:</b> {len(df)}", styles['Heading2'])
            story.append(summary)
        else:
            summary_table_data = [[summary_emoji, f"Total Options in Shortlist: {len(df)}"]]
            summary_table = Table(summary_table_data, colWidths=[0.3*inch, 5*inch])
            summary_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (1, 0), 14),
                ('TEXTCOLOR', (1, 0), (1, 0), HexColor('#667eea')),
            ]))
            story.append(summary_table)
        
        story.append(Spacer(1, 15))
        
# In generate_shortlist_pdf() function, replace the table generation section:

        if len(df) > 0:
            # Create styles for table cells with text wrapping
            cell_style = ParagraphStyle(
                'TableCellStyle',
                parent=styles['Normal'],
                fontSize=8,
                leading=10,
                alignment=1  # Center alignment
            )
            
            institute_cell_style = ParagraphStyle(
                'InstituteCellStyle',
                parent=styles['Normal'],
                fontSize=8,
                leading=10,
                alignment=0  # Left alignment for institutes
            )
            
            program_cell_style = ParagraphStyle(
                'ProgramCellStyle',
                parent=styles['Normal'],
                fontSize=8,
                leading=10,
                alignment=0  # Left alignment for programs
            )
            
            # Create table headers with emojis or fallback symbols
            emoji_headers = [
                emoji_manager.create_emoji_or_text('🏆', '#', 14, 14),
                emoji_manager.create_emoji_or_text('🏫', 'INST', 14, 14),
                emoji_manager.create_emoji_or_text('📚', 'PROG', 14, 14),
                emoji_manager.create_emoji_or_text('📊', 'RANK', 14, 14),
                emoji_manager.create_emoji_or_text('💺', 'SEAT', 14, 14),
                emoji_manager.create_emoji_or_text('🎟️', 'QUOTA', 14, 14),
                emoji_manager.create_emoji_or_text('👤', 'GENDER', 14, 14),
                emoji_manager.create_emoji_or_text('📝', 'NOTES', 14, 14)
            ]
            
            table_data = []
            
            # Header row with emojis or symbols
            table_data.append(emoji_headers)
            
            # Text labels row
            text_headers = ['Priority', 'Institute', 'Program', 'Closing Rank', 'Seat Type', 'Quota', 'Gender', 'Notes']
            table_data.append(text_headers)
            
            # Data rows with Paragraph objects for wrapping
            for _, row in df.iterrows():
                priority = str(int(row.get('priority_order', 0)))
                institute = str(row.get('institute', ''))
                program = str(row.get('program', ''))
                closing_rank = f"{int(row.get('closing_rank', 0)):,}"
                seat_type = str(row.get('seat_type', ''))
                quota = str(row.get('quota', ''))
                gender = str(row.get('gender', ''))
                notes = str(row.get('notes', '') or '')
                
                # Use Paragraph objects for text wrapping - NO TRUNCATION
                table_data.append([
                    Paragraph(priority, cell_style),
                    Paragraph(institute, institute_cell_style),  # Will wrap long names
                    Paragraph(program, program_cell_style),     # Will wrap long programs
                    Paragraph(closing_rank, cell_style),
                    Paragraph(seat_type, cell_style),
                    Paragraph(quota, cell_style),
                    Paragraph(gender, cell_style),
                    Paragraph(notes, cell_style)                # Will wrap long notes
                ])
            
            # Create table with appropriate column widths
            col_widths = [0.5*inch, 1.4*inch, 1.8*inch, 0.9*inch, 0.7*inch, 0.6*inch, 0.8*inch, 1.3*inch]
            table = Table(table_data, colWidths=col_widths, repeatRows=2)
            
            # Enhanced table style for wrapped text
            table_style = TableStyle([
                # Header rows
                ('BACKGROUND', (0, 0), (-1, 1), HexColor('#667eea')),
                ('TEXTCOLOR', (0, 1), (-1, 1), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Top align for wrapped text
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, 1), 9),
                
                # Data rows
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#dee2e6')),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 2), (-1, -1), [white, HexColor('#f8f9fa')])
            ])
            
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 30))
            
            # Enhanced statistics section
            generate_enhanced_statistics(df, story, styles, emoji_manager)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=HexColor('#666666'),
            alignment=TA_CENTER
        )
        
        footer = Paragraph("Generated by JEE Seat Finder | Keep this document for your college admission reference", footer_style)
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        
        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")


def validate_dataframe_for_pdf(df):
    """Validate DataFrame for PDF generation"""
    if df is None or len(df) == 0:
        return False
    
    required_columns = ['institute', 'program', 'closing_rank']
    return all(col in df.columns for col in required_columns)
