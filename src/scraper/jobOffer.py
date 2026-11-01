from dataclasses import dataclass, field
from datetime import datetime, timezone


SECTION_FIELDS = {
    'responsibilities': 'responsibilities',
    'requirements-expected': 'requirements',
    'requirements-optional': 'nice_to_have',
    'technologies-optional': 'technologies_optional',
    'offered': 'offered',
    'benefits': 'benefits',
    'training-space': 'training',
    'development-practices': 'development_practices',
    'work-organization-work-style': 'work_style',
    'recruitment-stages': 'recruitment_stages',
}

TEXT_SECTION_FIELDS = {
    'about-project': 'about_project',
    'about-us-description': 'about_company',
    'about-us': 'about_company',
    'about-hr-consulting-agency-client': 'about_company',
    'work-organization-team-size': 'team_size',
}

DESCRIPTION_SECTIONS = {
    'about-project': 'O projekcie',
    'responsibilities': 'Zakres obowiązków',
    'requirements-expected': 'Wymagania',
    'requirements-optional': 'Mile widziane',
    'offered': 'Oferujemy',
    'benefits': 'Benefity',
    'training-space': 'Rozwój',
}

DETAIL_FIELDS = (
    list(dict.fromkeys(SECTION_FIELDS.values()))
    + list(dict.fromkeys(TEXT_SECTION_FIELDS.values()))
    + ['description', 'details_fetched_at']
)


def clean_text(text):
    return ' '.join(text.replace(' ', ' ').split())


def parse_datetime(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


@dataclass
class JobOffer:
    """Model danych reprezentujący pojedynczą ofertę"""

    id: str
    title: str
    company: str | None = None
    salary: str | None = None
    url: str | None = None
    technologies: list[str] = field(default_factory=list)
    levels: list[str] = field(default_factory=list)
    contracts: list[str] = field(default_factory=list)
    work_modes: list[str] = field(default_factory=list)
    work_schedules: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    published_at: datetime | None = None
    expires_at: datetime | None = None

    description: str | None = None
    about_project: str | None = None
    about_company: str | None = None
    team_size: str | None = None
    responsibilities: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    nice_to_have: list[str] = field(default_factory=list)
    technologies_optional: list[str] = field(default_factory=list)
    offered: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    training: list[str] = field(default_factory=list)
    development_practices: list[str] = field(default_factory=list)
    work_style: list[str] = field(default_factory=list)
    recruitment_stages: list[str] = field(default_factory=list)
    details_fetched_at: datetime | None = None

    @classmethod
    def from_api(cls, offer_data):
        """Tworzy ofertę z jednego elementu 'groupedOffers' z listy ofert pracuj.pl."""
        sub_offers = offer_data.get('offers') or [{}]
        locations = [clean_text(s['displayWorkplace']) for s in sub_offers if s.get('displayWorkplace')]
        salary = offer_data.get('salaryDisplayText')
        return cls(
            id=offer_data['groupId'],
            title=clean_text(offer_data['jobTitle']),
            company=clean_text(offer_data['companyName']) if offer_data.get('companyName') else None,
            salary=clean_text(salary) if salary else None,
            url=sub_offers[0].get('offerAbsoluteUri'),
            technologies=offer_data.get('technologies') or [],
            levels=offer_data.get('positionLevels') or [],
            contracts=offer_data.get('typesOfContract') or [],
            work_modes=offer_data.get('workModes') or [],
            work_schedules=offer_data.get('workSchedules') or [],
            locations=list(dict.fromkeys(locations)),
            published_at=parse_datetime(offer_data.get('lastPublicated')),
            expires_at=parse_datetime(offer_data.get('expirationDate')),
        )

    def apply_details(self, sections):
        """Uzupełnia ofertę sekcjami ze strony szczegółów: {sectionType: [punkty]}."""
        for section_type, field_name in SECTION_FIELDS.items():
            setattr(self, field_name, sections.get(section_type, []))

        for section_type, field_name in TEXT_SECTION_FIELDS.items():
            if sections.get(section_type) and not getattr(self, field_name):
                setattr(self, field_name, '\n'.join(sections[section_type]))

        parts = []
        for section_type, title in DESCRIPTION_SECTIONS.items():
            items = sections.get(section_type)
            if items:
                parts.append(f"{title}:\n" + "\n".join(f"- {item}" for item in items))
        self.description = "\n\n".join(parts) or None
        self.details_fetched_at = datetime.now(timezone.utc)
