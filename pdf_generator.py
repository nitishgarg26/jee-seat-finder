# pdf_generator.py - HTML to PDF with full emoji support using WeasyPrint

import weasyprint
from weasyprint import HTML, CSS
import pandas as pd
import datetime
import io


def generate_shortlist_pdf(df, username):
    """
    Generate PDF using WeasyPrint (HTML to PDF) with full emoji support
    
    Args:
        df (pandas.DataFrame): Shortlist data
        username (str): User's name for the report
    
    Returns:
        bytes: PDF file as bytes
    """
    try:
        # Calculate statistics
        if len(df) > 0:
            avg_rank = df['closing_rank'].mean()
            min_rank = df['closing_rank'].min()
            max_rank = df['closing_rank'].max()
            institute_counts = df['institute'].value_counts().head(5)
            seat_type_counts = df['seat_type'].value_counts()
        
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        
        # Create HTML content with emojis
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>JEE Seat Finder - Shortlist</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Noto+Color+Emoji&family=Inter:wght@400;600;700&display=swap');
                
                body {{
                    font-family: 'Inter', 'Noto Color Emoji', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 3px solid #667eea;
                }}
                
                .title {{
                    color: #667eea;
                    font-size: 24px;
                    font-weight: 700;
                    margin-bottom: 10px;
                }}
                
                .subtitle {{
                    color: #666;
                    font-size: 14px;
                }}
                
                .summary {{
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    text-align: center;
                    font-weight: 600;
                }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: 11px;
                }}
                
                th {{
                    background: #667eea;
                    color: white;
                    padding: 12px 8px;
                    text-align: center;
                    font-weight: 600;
                }}
                
                td {{
                    padding: 10px 8px;
                    text-align: center;
                    border-bottom: 1px solid #eee;
                }}
                
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                
                tr:hover {{
                    background-color: #e3f2fd;
                }}
                
                .stats-section {{
                    margin: 30px 0;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    border-left: 4px solid #667eea;
                }}
                
                .stats-title {{
                    color: #667eea;
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 15px;
                }}
                
                .stats-item {{
                    margin: 8px 0;
                    padding: 5px 0;
                }}
                
                .highlight {{
                    background: #fff3cd;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-weight: 600;
                }}
                
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    color: #666;
                    font-size: 12px;
                }}
                
                @page {{
                    size: A4;
                    margin: 1cm;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">🎓 JEE Seat Finder - My Shortlist</div>
                <div class="subtitle">
                    <strong>Student:</strong> {username} | 
                    <strong>Generated on:</strong> {current_date}
                </div>
            </div>
            
            <div class="summary">
                📊 Total Options in Shortlist: {len(df)}
            </div>
        """
        
        if len(df) > 0:
            # Add table
            html_content += """
            <table>
                <thead>
                    <tr>
                        <th>🏆 Priority</th>
                        <th>🏫 Institute</th>
                        <th>📚 Program</th>
                        <th>📊 Closing Rank</th>
                        <th>💺 Seat Type</th>
                        <th>🎟️ Quota</th>
                        <th>👤 Gender</th>
                        <th>📝 Notes</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for _, row in df.iterrows():
                priority = int(row.get('priority_order', 0))
                institute = str(row.get('institute', ''))
                program = str(row.get('program', ''))
                closing_rank = f"{int(row.get('closing_rank', 0)):,}"
                seat_type = str(row.get('seat_type', ''))
                quota = str(row.get('quota', ''))
                gender = str(row.get('gender', ''))
                notes = str(row.get('notes', '') or '')
                
                # Truncate long text
                if len(institute) > 25:
                    institute = institute[:25] + "..."
                if len(program) > 30:
                    program = program[:30] + "..."
                if len(notes) > 20:
                    notes = notes[:20] + "..."
                
                html_content += f"""
                    <tr>
                        <td>{priority}</td>
                        <td>{institute}</td>
                        <td>{program}</td>
                        <td>{closing_rank}</td>
                        <td>{seat_type}</td>
                        <td>{quota}</td>
                        <td>{gender}</td>
                        <td>{notes}</td>
                    </tr>
                """
            
            html_content += "</tbody></table>"
            
            # Add statistics
            html_content += f"""
            <div class="stats-section">
                <div class="stats-title">📈 Summary Statistics</div>
                
                <div class="stats-item">
                    <strong>📊 Rank Analysis:</strong>
                </div>
                <div class="stats-item">• Average Closing Rank: <span class="highlight">{int(avg_rank):,}</span></div>
                <div class="stats-item">• Best Rank (Lowest): <span class="highlight">{int(min_rank):,}</span></div>
                <div class="stats-item">• Highest Rank: <span class="highlight">{int(max_rank):,}</span></div>
                <div class="stats-item">• Rank Range: <span class="highlight">{int(max_rank - min_rank):,}</span> positions</div>
                
                <div class="stats-item" style="margin-top: 20px;">
                    <strong>🏫 Top Institutes:</strong>
                </div>
            """
            
            for institute, count in institute_counts.items():
                percentage = (count / len(df)) * 100
                html_content += f'<div class="stats-item">• {institute}: <span class="highlight">{count}</span> option{"s" if count > 1 else ""} ({percentage:.1f}%)</div>'
            
            html_content += f"""
                <div class="stats-item" style="margin-top: 20px;">
                    <strong>💺 Seat Type Distribution:</strong>
                </div>
            """
            
            for seat_type, count in seat_type_counts.items():
                percentage = (count / len(df)) * 100
                html_content += f'<div class="stats-item">• {seat_type}: <span class="highlight">{count}</span> option{"s" if count > 1 else ""} ({percentage:.1f}%)</div>'
            
            html_content += "</div>"
        
        else:
            html_content += "<p style='text-align: center; margin: 40px 0; color: #666;'>No items in shortlist yet.</p>"
        
        # Close HTML
        html_content += """
            <div class="footer">
                Generated by JEE Seat Finder | Keep this document for your college admission reference
            </div>
        </body>
        </html>
        """
        
        # Generate PDF from HTML
        html_doc = HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        return pdf_bytes
        
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")


def validate_dataframe_for_pdf(df):
    """Validate DataFrame for PDF generation"""
    if df is None or len(df) == 0:
        return False
    
    required_columns = ['institute', 'program', 'closing_rank']
    return all(col in df.columns for col in required_columns)
