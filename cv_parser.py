import pdfplumber
import re
from bs4 import BeautifulSoup
import os

class CVParser:
    def __init__(self, pdf_path, html_path):
        self.pdf_path = pdf_path
        self.html_path = html_path
        self.data = {
            'name': '',
            'profession': '',
            'tagline': '',
            'about': [],
            'experience': [],
            'education': [],
            'skills': {
                'technical': [],
                'professional': []
            },
            'contact': {
                'email': 'your.email@example.com',
                'phone': '+92 XXX XXXXXXX',
                'location': '[Your Location]',
                'social': {
                    'linkedin': '#',
                    'github': '#',
                    'twitter': '#',
                    'facebook': '#'
                }
            }
        }

    def extract_text_from_pdf(self):
        """Extract text from the PDF file."""
        text = ""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text

    def parse_cv(self):
        """Parse the CV text to extract relevant information."""
        text = self.extract_text_from_pdf()
        
        # Split text into lines and clean up
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Extract name (assuming it's the first non-empty line)
        if lines:
            self.data['name'] = lines[0]
        
        # Extract contact information (email, phone)
        for line in lines:
            # Extract email
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', line)
            if email_match:
                self.data['contact']['email'] = email_match.group(0)
            
            # Extract phone number (various formats)
            phone_match = re.search(r'(\+\d{1,3}[-.\s]?)?(\d{3}[-.\s]?){2,4}\d{3,4}', line)
            if phone_match and len(phone_match.group(0).replace(' ', '')) >= 10:
                self.data['contact']['phone'] = phone_match.group(0).strip()
        
        # Simple extraction of sections (this is a basic implementation)
        current_section = None
        for line in lines:
            line_lower = line.lower()
            
            # Detect section headers
            if 'experience' in line_lower or 'work' in line_lower and 'experience' in line_lower:
                current_section = 'experience'
                continue
            elif 'education' in line_lower:
                current_section = 'education'
                continue
            elif 'skills' in line_lower or 'expertise' in line_lower:
                current_section = 'skills'
                continue
            elif 'about' in line_lower or 'summary' in line_lower:
                current_section = 'about'
                continue
            
            # Add content to the current section
            if current_section == 'experience' and line.strip() and len(line.split()) > 3:
                self.data['experience'].append(line)
            elif current_section == 'education' and line.strip() and len(line.split()) > 2:
                self.data['education'].append(line)
            elif current_section == 'skills' and line.strip():
                # Categorize skills (this is a simple approach)
                if any(skill in line_lower for skill in ['programming', 'technical', 'tools', 'languages']):
                    self.data['skills']['technical'].extend([s.strip() for s in re.split(r'[,;]', line) if s.strip()])
                else:
                    self.data['skills']['professional'].extend([s.strip() for s in re.split(r'[,;]', line) if s.strip()])
            elif current_section == 'about' and line.strip():
                self.data['about'].append(line)
        
        return self.data

    def update_html(self):
        """Update the HTML file with the extracted CV data."""
        with open(self.html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        # Update name and profession in hero section
        hero = soup.find('section', {'id': 'home'})
        if hero:
            name_h1 = hero.find('h1')
            if name_h1:
                name_h1.string = self.data.get('name', name_h1.string)
            
            profession_p = hero.find('p', class_='profession')
            if profession_p and self.data.get('profession'):
                profession_p.string = self.data['profession']
        
        # Update about section
        about_section = soup.find('section', {'id': 'about'})
        if about_section and self.data.get('about'):
            about_text = about_section.find('div', class_='about-text')
            if about_text:
                # Clear existing paragraphs
                for p in about_text.find_all('p'):
                    p.decompose()
                
                # Add new paragraphs from CV
                for paragraph in self.data['about']:
                    p_tag = soup.new_tag('p')
                    p_tag.string = paragraph
                    about_text.append(p_tag)
                
                # Update contact info
                contact_info = about_text.find('div', class_='personal-info')
                if contact_info:
                    for item in contact_info.find_all('div', class_='info-item'):
                        label = item.find('span', class_='info-label')
                        if label and 'email' in label.text.lower():
                            item.find('span', class_='info-value').string = self.data['contact']['email']
                        elif label and 'phone' in label.text.lower():
                            item.find('span', class_='info-value').string = self.data['contact']['phone']
        
        # Update experience section
        experience_section = soup.find('section', {'id': 'experience'})
        if experience_section and self.data.get('experience'):
            timeline = experience_section.find('div', class_='timeline')
            if timeline:
                # Clear existing items
                for item in timeline.find_all('div', class_='timeline-item'):
                    item.decompose()
                
                # Add experience items from CV
                for exp in self.data['experience']:
                    # This is a simplified example - you might want to parse the experience more thoroughly
                    item_div = soup.new_tag('div', **{'class': 'timeline-item'})
                    dot_div = soup.new_tag('div', **{'class': 'timeline-dot'})
                    content_div = soup.new_tag('div', **{'class': 'timeline-content'})
                    
                    # Parse the experience line (this is a simple approach)
                    # In a real scenario, you'd want to parse dates, company names, etc.
                    h3 = soup.new_tag('h3')
                    h3.string = exp.split(' at ')[0] if ' at ' in exp else exp.split(' - ')[0] if ' - ' in exp else exp
                    
                    company_span = soup.new_tag('span', **{'class': 'company'})
                    if ' at ' in exp:
                        company_span.string = exp.split(' at ')[1].split(' (')[0] if ' (' in exp else exp.split(' at ')[1]
                    
                    date_span = soup.new_tag('span', **{'class': 'date'})
                    date_span.string = 'Date not specified'  # You would extract this from the CV
                    
                    ul = soup.new_tag('ul')
                    li = soup.new_tag('li')
                    li.string = exp
                    ul.append(li)
                    
                    content_div.append(h3)
                    content_div.append(company_span)
                    content_div.append(date_span)
                    content_div.append(ul)
                    
                    item_div.append(dot_div)
                    item_div.append(content_div)
                    timeline.append(item_div)
        
        # Update education section
        education_section = soup.find('section', {'id': 'education'})
        if education_section and self.data.get('education'):
            education_grid = education_section.find('div', class_='education-grid')
            if education_grid:
                # Clear existing items
                for item in education_grid.find_all('div', class_='education-item'):
                    item.decompose()
                
                # Add education items from CV
                for edu in self.data['education']:
                    item_div = soup.new_tag('div', **{'class': 'education-item'})
                    
                    h3 = soup.new_tag('h3')
                    h3.string = edu.split(' at ')[0] if ' at ' in edu else edu.split(', ')[0] if ', ' in edu else edu
                    
                    institution_p = soup.new_tag('p', **{'class': 'institution'})
                    if ' at ' in edu:
                        institution_p.string = edu.split(' at ')[1].split(' (')[0] if ' (' in edu else edu.split(' at ')[1]
                    
                    duration_p = soup.new_tag('p', **{'class': 'duration'})
                    duration_p.string = 'Date not specified'  # You would extract this from the CV
                    
                    description_p = soup.new_tag('p', **{'class': 'description'})
                    description_p.string = edu
                    
                    item_div.append(h3)
                    item_div.append(institution_p)
                    item_div.append(duration_p)
                    item_div.append(description_p)
                    
                    education_grid.append(item_div)
        
        # Update skills section
        skills_section = soup.find('section', {'id': 'skills'})
        if skills_section and self.data.get('skills'):
            # Update technical skills
            technical_skills = skills_section.find('div', class_='skill-category')
            if technical_skills and self.data['skills'].get('technical'):
                tags_div = technical_skills.find('div', class_='skill-tags')
                if tags_div:
                    tags_div.clear()
                    for skill in self.data['skills']['technical'][:10]:  # Limit to 10 skills
                        if len(skill) > 2:  # Filter out very short strings
                            tag = soup.new_tag('span', **{'class': 'skill-tag'})
                            tag.string = skill.strip()
                            tags_div.append(tag)
            
            # Update professional skills
            professional_skills = skills_section.find_all('div', class_='skill-category')
            if len(professional_skills) > 1 and self.data['skills'].get('professional'):
                tags_div = professional_skills[1].find('div', class_='skill-tags')
                if tags_div:
                    tags_div.clear()
                    for skill in self.data['skills']['professional'][:10]:  # Limit to 10 skills
                        if len(skill) > 2:  # Filter out very short strings
                            tag = soup.new_tag('span', **{'class': 'skill-tag'})
                            tag.string = skill.strip()
                            tags_div.append(tag)
        
        # Update contact information
        contact_section = soup.find('section', {'id': 'contact'})
        if contact_section:
            # Update email
            email_item = contact_section.find('i', class_='fa-envelope')
            if email_item and self.data['contact'].get('email'):
                email_item.parent.find('p').string = self.data['contact']['email']
            
            # Update phone
            phone_item = contact_section.find('i', class_='fa-phone')
            if phone_item and self.data['contact'].get('phone'):
                phone_item.parent.find('p').string = self.data['contact']['phone']
            
            # Update location
            location_item = contact_section.find('i', class_='fa-map-marker-alt')
            if location_item and self.data['contact'].get('location'):
                location_item.parent.find('p').string = self.data['contact']['location']
            
            # Update social links
            social_links = contact_section.find('div', class_='social-links')
            if social_links and self.data['contact'].get('social'):
                for a in social_links.find_all('a'):
                    icon = a.find('i')
                    if 'linkedin' in str(icon):
                        a['href'] = self.data['contact']['social']['linkedin']
                    elif 'github' in str(icon):
                        a['href'] = self.data['contact']['social']['github']
                    elif 'twitter' in str(icon):
                        a['href'] = self.data['contact']['social']['twitter']
                    elif 'facebook' in str(icon):
                        a['href'] = self.data['contact']['social']['facebook']
        
        # Save the updated HTML
        with open(self.html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))

if __name__ == "__main__":
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define file paths
    pdf_path = os.path.join(current_dir, 'M Sameer Khan-CV.pdf')
    html_path = os.path.join(current_dir, 'index.html')
    
    # Create parser instance and process CV
    parser = CVParser(pdf_path, html_path)
    cv_data = parser.parse_cv()
    
    # Update the HTML file
    parser.update_html()
    
    print("CV processing complete! The webpage has been updated with your CV information.")
    print("You can now open the index.html file in your browser to see the updated profile.")
