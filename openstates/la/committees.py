from billy.scrape import NoDataForPeriod
from billy.scrape.committees import CommitteeScraper, Committee

import lxml.html


class LACommitteeScraper(CommitteeScraper):
    jurisdiction = 'la'

    def scrape(self, chamber, term):
        if term != self.metadata['terms'][-1]['name']:
            raise NoDataForPeriod(term)

        if chamber == 'upper':
            self.scrape_senate()
        else:
            self.scrape_house()

    def scrape_senate(self):
        url = 'http://senate.legis.state.la.us/Committees/default.asp'
        text = self.urlopen(url)
        page = lxml.html.fromstring(text)
        page.make_links_absolute(url)

        links = page.xpath('//b[contains(text(), "Standing Committees")]'
                           '/../following-sibling::font/ul/li/a')

        for link in links:
            name = link.xpath('string()')
            url = link.attrib['href']

            self.scrape_senate_committee(name, url)

    def scrape_senate_committee(self, name, url):
        url = url.replace('Default.asp', 'Assignments.asp')

        committee = Committee('upper', name)
        committee.add_source(url)

        text = self.urlopen(url)
        page = lxml.html.fromstring(text)

        links = page.xpath('//table[@bordercolor="#EBEAEC"]/tr/td/font/a')

        for link in links:
            role = "member"
            if link.tail:
                role = link.tail.strip().strip("() ")

            name = link.xpath('string()')
            name = name.replace('Senator ', '').strip()

            committee.add_member(name, role)

        self.save_committee(committee)

    def scrape_house(self):
        url = "http://house.louisiana.gov/H_Reps/H_Reps_CmtesFull.asp"
        comm_cache = {}
        text = self.urlopen(url)
        page = lxml.html.fromstring(text)

        for row in page.xpath("//table[@bordercolorlight='#EAEAEA']/tr"):
            cells = row.xpath('td')

            name = cells[0].xpath('string()').strip()

            if name.startswith('Vacant'):
                continue

            font = cells[1]
            committees = []

            if font is not None and font.text:
                committees.append(font.text.strip())
            for br in font.xpath('br'):
                if br.text:
                    committees.append(br.text.strip())
                if br.tail:
                    committees.append(br.tail)

            for comm_name in committees:
                mtype = 'member'
                if comm_name.endswith(', Chairman'):
                    mtype = 'chairman'
                    comm_name = comm_name.replace(', Chairman', '')
                elif comm_name.endswith(', Co-Chairmain'):
                    mtype = 'co-chairmain'
                    comm_name = comm_name.replace(', Co-Chairmain', '')
                elif comm_name.endswith(', Vice Chair'):
                    mtype = 'vice chair'
                    comm_name = comm_name.replace(', Vice Chair', '')
                elif comm_name.endswith(', Ex Officio'):
                    mtype = 'ex officio'
                    comm_name = comm_name.replace(', Ex Officio', '')
                elif comm_name.endswith(", Interim Member"):
                    mtype = 'interim'
                    comm_name = comm_name.replace(", Interim Member", "")


                if comm_name.startswith('Joint'):
                    chamber = 'joint'
                else:
                    chamber = 'lower'

                try:
                    committee = comm_cache[comm_name]
                except KeyError:
                    committee = Committee(chamber, comm_name)
                    committee.add_source(url)
                    comm_cache[comm_name] = committee

                committee.add_member(name, mtype)

        for committee in comm_cache.values():
            self.save_committee(committee)
