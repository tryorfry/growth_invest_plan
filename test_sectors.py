from src.data_sources.sector_source import SectorSource
import pprint

src = SectorSource()
data = src.fetch_sector_performance()
pprint.pprint(data)
