# pdf_generator.py - PDF generation with ReportLab (supports emojis)

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import datetime
import pandas as pd
import io


def generate_shortlist_pdf(df, username):
    """
    Generate a well-formatted PDF from shortlist DataFrame using ReportLab
    
    Args:
        df (pandas.DataFrame): Shortlist data
        username (str): User's name for the report
    
    Returns:
        bytes: PDF file as bytes
    """
    try:
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
        
        # Title with emoji
        title = Paragraph("🎓 JEE Seat Finder - My Shortlist", title_style)
        story.append(title)
        
        # User info
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        user_info = Paragraph(f"<b>Student:</b> {username} | <b>Generated on:</b> {current_date}", subtitle_style)
        story.append(user_info)
        story.append(Spacer(1, 20))
        
        # Summary
        summary = Paragraph(f"📊 <b>Total Options in Shortlist:</b> {len(df)}", heading_style)
        story.append(summary)
        story.append(Spacer(1, 15))
        
        if len(df) == 0:
            no_data = Paragraph("No items in shortlist yet.", normal_style)
            story.append(no_data)
        else:
            # Create table data
            table_data = [
                ['🏆\nPriority', '🏫\nInstitute', '📚\nProgram', '📊\nClosing Rank', '💺\nSeat Type', '🎟️\nQuota', '👤\nGender', '📝\nNotes']
            ]
            
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
                if len(institute) > 20:
                    institute = institute[:20] + "..."
                if len(program) > 25:
                    program = program[:25] + "..."
                if len(notes) > 15:
                    notes = notes[:15] + "..."
                
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
            col_widths = [0.6*inch, 1.4*inch, 1.8*inch, 1*inch, 0.8*inch, 0.6*inch, 0.8*inch, 1*inch]
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # Table style
            table_style = TableStyle([
                # Header row styling
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                
                # Data rows styling
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#dee2e6')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')])
            ])
            
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 30))
            
            # Statistics section
            stats_title = Paragraph("📈 Summary Statistics", heading_style)
            story.append(stats_title)
            story.append(Spacer(1, 10))
            
            # Calculate statistics
            avg_rank = df['closing_rank'].mean()
            min_rank = df['closing_rank'].min()
            max_rank = df['closing_rank'].max()
            
            # Rank statistics
            rank_stats = f"""
            <b>📊 Rank Analysis:</b><br/>
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
                institute_stats = "<b>🏫 Institute Distribution:</b><br/>"
                for institute, count in institute_counts.items():
                    percentage = (count / len(df)) * 100
                    institute_stats += f"• {institute}: <b>{count}</b> option{'s' if count > 1 else ''} ({percentage:.1f}%)<br/>"
                
                institute_para = Paragraph(institute_stats, normal_style)
                story.append(institute_para)
                story.append(Spacer(1, 15))
            
            # Seat type breakdown
            seat_type_counts = df['seat_type'].value_counts()
            if len(seat_type_counts) > 0:
                seat_stats = "<b>💺 Seat Type Distribution:</b><br/>"
                for seat_type, count in seat_type_counts.items():
                    percentage = (count / len(df)) * 100
                    seat_stats += f"• {seat_type}: <b>{count}</b> option{'s' if count > 1 else ''} ({percentage:.1f}%)<br/>"
                
                seat_para = Paragraph(seat_stats, normal_style)
                story.append(seat_para)
                story.append(Spacer(1, 15))
            
            # Quota breakdown
            quota_counts = df['quota'].value_counts()
            if len(quota_counts) > 0:
                quota_stats = "<b>🎟️ Quota Distribution:</b><br/>"
                for quota, count in quota_counts.items():
                    percentage = (count / len(df)) * 100
                    quota_stats += f"• {quota}: <b>{count}</b> option{'s' if count > 1 else ''} ({percentage:.1f}%)<br/>"
                
                quota_para = Paragraph(quota_stats, normal_style)
                story.append(quota_para)
        
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


def generate_search_results_pdf(df, username, filters_applied=None):
    """
    Generate PDF for search results
    
    Args:
        df (pandas.DataFrame): Search results data
        username (str): User's name
        filters_applied (dict): Applied filters information
    
    Returns:
        bytes: PDF file as bytes
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=72, bottomMargin=50)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, 
                                    spaceAfter=30, textColor=HexColor('#667eea'), alignment=TA_CENTER)
        title = Paragraph("🔍 JEE Seat Finder - Search Results", title_style)
        story.append(title)
        
        # User and date info
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        user_info = Paragraph(f"<b>User:</b> {username} | <b>Generated on:</b> {current_date}", styles['Normal'])
        story.append(user_info)
        story.append(Spacer(1, 20))
        
        # Results summary
        summary = Paragraph(f"📊 <b>Found {len(df)} matching programs</b>", styles['Heading2'])
        story.append(summary)
        story.append(Spacer(1, 15))
        
        # Applied filters
        if filters_applied:
            filters_title = Paragraph("🔧 Applied Filters:", styles['Heading3'])
            story.append(filters_title)
            
            filter_text = ""
            for filter_name, filter_value in filters_applied.items():
                if filter_value:
                    filter_text += f"• {filter_name}: {filter_value}<br/>"
            
            if filter_text:
                filters_para = Paragraph(filter_text, styles['Normal'])
                story.append(filters_para)
            
            story.append(Spacer(1, 20))
        
        # Results table (limit to first 100 for performance)
        display_df = df.head(100)
        
        table_data = [['🏫 Institute', '📚 Program', '📊 Closing Rank', '💺 Seat Type', '🎟️ Quota', '👤 Gender']]
        
        for _, row in display_df.iterrows():
            institute = str(row.get('Institute', ''))[:25]
            program = str(row.get('Academic Program Name', ''))[:30]
            closing_rank = f"{int(row.get('Closing Rank', 0)):,}"
            seat_type = str(row.get('Seat Type', ''))
            quota = str(row.get('Quota', ''))
            gender = str(row.get('Gender', ''))[:15]
            
            table_data.append([institute, program, closing_rank, seat_type, quota, gender])
        
        # Create table
        table = Table(table_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1*inch, 0.8*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#dee2e6')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')])
        ]))
        
        story.append(table)
        
        if len(df) > 100:
            note = Paragraph(f"<i>Note: Showing first 100 results out of {len(df)} total matches.</i>", styles['Normal'])
            story.append(Spacer(1, 15))
            story.append(note)
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        raise Exception(f"Search results PDF generation failed: {str(e)}")


def validate_dataframe_for_pdf(df):
    """
    Validate that the DataFrame has required columns for PDF generation
    
    Args:
        df (pandas.DataFrame): DataFrame to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if df is None or len(df) == 0:
        return False
    
    required_columns = ['institute', 'program', 'closing_rank']
    return all(col in df.columns for col in required_columns)
