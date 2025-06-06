# pdf_generator.py - ReportLab with actual emoji support

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfutils
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import datetime
import pandas as pd
import io
import requests
import os


def setup_emoji_font():
    """Download and register a Unicode font that supports emojis"""
    font_path = "NotoColorEmoji.ttf"
    fallback_font_path = "DejaVuSans.ttf"
    
    # Try to use Noto Color Emoji first (best emoji support)
    if not os.path.exists(font_path):
        try:
            # Download Noto Sans (supports many Unicode characters including some emojis)
            font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf"
            response = requests.get(font_url, timeout=10)
            with open(font_path, 'wb') as f:
                f.write(response.content)
        except:
            # Fallback to DejaVu Sans
            if not os.path.exists(fallback_font_path):
                try:
                    fallback_url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
                    response = requests.get(fallback_url, timeout=10)
                    with open(fallback_font_path, 'wb') as f:
                        f.write(response.content)
                    font_path = fallback_font_path
                except:
                    return None, None
    
    try:
        # Register the font with ReportLab
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('EmojiFont', font_path))
            return 'EmojiFont', font_path
        elif os.path.exists(fallback_font_path):
            pdfmetrics.registerFont(TTFont('EmojiFont', fallback_font_path))
            return 'EmojiFont', fallback_font_path
    except Exception as e:
        print(f"Font registration failed: {e}")
    
    return None, None


def generate_shortlist_pdf(df, username):
    """
    Generate a well-formatted PDF with emoji support
    """
    try:
        # Setup emoji font
        emoji_font, font_path = setup_emoji_font()
        
        # Create a BytesIO buffer
        buffer = io.BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=72,
            bottomMargin=50
        )
        
        # Build the PDF content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles with emoji font if available
        if emoji_font:
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=30,
                textColor=HexColor('#667eea'),
                alignment=TA_CENTER,
                fontName=emoji_font
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                textColor=HexColor('#667eea'),
                fontName=emoji_font
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                fontName=emoji_font
            )
        else:
            # Fallback to regular fonts
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=30,
                textColor=HexColor('#667eea'),
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                textColor=HexColor('#667eea'),
                fontName='Helvetica-Bold'
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6
            )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            textColor=HexColor('#333333'),
            alignment=TA_CENTER
        )
        
        # Title with emoji (will display if font supports it)
        title_text = "🎓 JEE Seat Finder - My Shortlist" if emoji_font else "JEE Seat Finder - My Shortlist"
        title = Paragraph(title_text, title_style)
        story.append(title)
        
        # User info
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        user_info = Paragraph(f"<b>Student:</b> {username} | <b>Generated on:</b> {current_date}", subtitle_style)
        story.append(user_info)
        story.append(Spacer(1, 20))
        
        # Summary with emoji
        summary_text = f"📊 <b>Total Options in Shortlist:</b> {len(df)}" if emoji_font else f"<b>Total Options in Shortlist:</b> {len(df)}"
        summary = Paragraph(summary_text, heading_style)
        story.append(summary)
        story.append(Spacer(1, 15))
        
        if len(df) == 0:
            no_data = Paragraph("No items in shortlist yet.", normal_style)
            story.append(no_data)
        else:
            # Create table data with emojis if supported
            if emoji_font:
                headers = ['🏆', '🏫 Institute', '📚 Program', '📊 Rank', '💺 Type', '🎟️ Quota', '👤 Gender', '📝 Notes']
            else:
                headers = ['#', 'Institute', 'Program', 'Closing Rank', 'Seat Type', 'Quota', 'Gender', 'Notes']
            
            table_data = [headers]
            
            for _, row in df.iterrows():
                # Handle None values and format data
                priority = str(int(row.get('priority_order', 0)))
                institute = str(row.get('institute', ''))
                program = str(row.get('program', ''))
                closing_rank = f"{int(row.get('closing_rank', 0)):,}"
                seat_type = str(row.get('seat_type', ''))
                quota = str(row.get('quota', ''))
                gender = str(row.get('gender', ''))
                notes = str(row.get('notes', '') or '')
                
                # Truncate long text for better table formatting
                if len(institute) > 22:
                    institute = institute[:22] + "..."
                if len(program) > 28:
                    program = program[:28] + "..."
                if len(notes) > 18:
                    notes = notes[:18] + "..."
                
                table_data.append([
                    priority,
                    institute,
                    program,
                    closing_rank,
                    seat_type,
                    quota,
                    gender,
                    notes
                ])
            
            # Create table with appropriate column widths
            col_widths = [0.4*inch, 1.5*inch, 2*inch, 0.8*inch, 0.7*inch, 0.6*inch, 0.8*inch, 1.2*inch]
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # Table style
            table_style = TableStyle([
                # Header row styling
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), emoji_font if emoji_font else 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                
                # Data rows styling
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
                ('FONTNAME', (0, 1), (-1, -1), emoji_font if emoji_font else 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#dee2e6')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')])
            ])
            
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 30))
            
            # Statistics section with emojis
            stats_title_text = "📈 Summary Statistics" if emoji_font else "Summary Statistics"
            stats_title = Paragraph(stats_title_text, heading_style)
            story.append(stats_title)
            story.append(Spacer(1, 10))
            
            # Calculate statistics
            avg_rank = df['closing_rank'].mean()
            min_rank = df['closing_rank'].min()
            max_rank = df['closing_rank'].max()
            
            # Rank statistics with emojis if available
            if emoji_font:
                rank_stats = f"""
                <b>📊 Rank Analysis:</b><br/>
                • Average Closing Rank: <b>{int(avg_rank):,}</b><br/>
                • Best Rank (Lowest): <b>{int(min_rank):,}</b><br/>
                • Highest Rank: <b>{int(max_rank):,}</b><br/>
                • Rank Range: <b>{int(max_rank - min_rank):,}</b> positions<br/>
                """
            else:
                rank_stats = f"""
                <b>Rank Analysis:</b><br/>
                • Average Closing Rank: <b>{int(avg_rank):,}</b><br/>
                • Best Rank (Lowest): <b>{int(min_rank):,}</b><br/>
                • Highest Rank: <b>{int(max_rank):,}</b><br/>
                • Rank Range: <b>{int(max_rank - min_rank):,}</b> positions<br/>
                """
            
            rank_para = Paragraph(rank_stats, normal_style)
            story.append(rank_para)
            story.append(Spacer(1, 15))
            
            # Institute breakdown
            institute_counts = df['institute'].value_counts().head(5)
            if len(institute_counts) > 0:
                institute_header = "🏫 Institute Distribution:" if emoji_font else "Institute Distribution:"
                institute_stats = f"<b>{institute_header}</b><br/>"
                for institute, count in institute_counts.items():
                    percentage = (count / len(df)) * 100
                    institute_stats += f"• {institute}: <b>{count}</b> option{'s' if count > 1 else ''} ({percentage:.1f}%)<br/>"
                
                institute_para = Paragraph(institute_stats, normal_style)
                story.append(institute_para)
                story.append(Spacer(1, 15))
            
            # Seat type breakdown
            seat_type_counts = df['seat_type'].value_counts()
            if len(seat_type_counts) > 0:
                seat_header = "💺 Seat Type Distribution:" if emoji_font else "Seat Type Distribution:"
                seat_stats = f"<b>{seat_header}</b><br/>"
                for seat_type, count in seat_type_counts.items():
                    percentage = (count / len(df)) * 100
                    seat_stats += f"• {seat_type}: <b>{count}</b> option{'s' if count > 1 else ''} ({percentage:.1f}%)<br/>"
                
                seat_para = Paragraph(seat_stats, normal_style)
                story.append(seat_para)
        
        # Footer information
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
