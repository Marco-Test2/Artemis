import os

from PySide6.QtCore import QUrl
from datetime import datetime

from artemis.utils.constants import Constants
from artemis.utils.generic_utils import format_frequency
from artemis.utils.path_utils import DATA_DIR

from artemis.model import (
    database, Info, Signals, Category, CategoryLabel, Frequency, Bandwidth, 
    Modulation, Mode, Location, Acf, Documents
)
from peewee import SqliteDatabase, IntegerField
from playhouse.migrate import SqliteMigrator, migrate


################################## MARK: ==== DATABASE ====
class ArtemisDB:
    def __init__(self, db_dir_name, apply_migrations=False):
        self.db_dir_name = db_dir_name
        self.db_dir = DATA_DIR / db_dir_name
        self.sql_path = self.db_dir / Constants.SQL_NAME
        self.media_dir = self.db_dir / 'media'

        self.name = None
        self.date = None
        self.version = None
        self.editable = None

        self.all_signals = []
        self.all_modulations = []
        self.all_locations = []
        self.all_category_labels = []

        db_original = SqliteDatabase(self.sql_path)
        database.initialize(db_original)

        # If DB exixts -> apply migrations (if required, not default) and load
        # if DB does not exist -> does nothing. Wait for calling create method
        if self.sql_path.exists():
            with database:
                if apply_migrations:
                    self.migrate_db()

                self.load()


    def load(self):
        """ Load all the initial data: info, a list of all signals (used for the main
            signals list, all the categories-locations-modulations (used to populate
            the filters combobox) 
        """
        self._load_info()
        self._select_all_signals()
        self._select_all_category_labels()
        self._select_all_locations()
        self._select_all_modulations()


    def _load_info(self):
        """ Load the DB meta INFO from the table 'info'
        """
        try:
            info_record = Info.select().first()
            if info_record:
                self.name = info_record.name
                self.date = info_record.date
                self.version = info_record.version
                self.editable = info_record.editable
        except Exception as e:
            print(f"ERROR: {e}")


    def _select_all_signals(self):
        """ Load a list of tuple for all signals. Each tuple (representing a signal)
            contains the SIG_ID, NAME adn DESCRITPION of the signal
        """
        try:
            query = Signals.select(
                Signals.sig_id, 
                Signals.name, 
                Signals.description
            ).dicts()
            self.all_signals = list(query)
        except Exception as e:
            print(f"ERROR: {e}")
            self.all_signals = []


    def _select_all_modulations(self):
        try:
            query = Modulation.select(Modulation.value).distinct().order_by(Modulation.value).dicts()
            self.all_modulations = list(query)
        except Exception as e:
            print(f"ERROR: {e}")
            self.all_modulations = []


    def _select_all_locations(self):
        try:
            query = Location.select(Location.value).distinct().order_by(Location.value).dicts()
            self.all_locations = list(query)
        except Exception as e:
            print(f"ERROR: {e}")
            self.all_locations = []


    def _select_all_category_labels(self):
        try:
            query = CategoryLabel.select(
                CategoryLabel.clb_id, 
                CategoryLabel.value
            ).distinct().order_by(CategoryLabel.value).dicts()
            self.all_category_labels = list(query)
        except Exception as e:
            print(f"ERROR: {e}")
            self.all_category_labels = []

################################## MARK: MIGRATIONS
    def migrate_db(self):
        """ if models.py is changed and then the DB schema , hre goes al the necessary 
            migrations to assure the compatibility of older DB. MIGRATION 1 and 2 has been
            introduced during the ORM implementation.
        """
        migrator = SqliteMigrator(database)

        # MIGRATION 1
        # Introduction of a new column called since_version in the signals table
        since_version_field = IntegerField(column_name='SINCE_VERSION', null=True)
        try:
            migrate(migrator.add_column('signals', 'SINCE_VERSION', since_version_field))
        except Exception:
            pass

        # MIGRATION 2
        # renamed the table category_label to categorylabel. The latter is peewee standard
        # nomencalture so the meta block in model.py is not necessary
        try:
            migrate(migrator.rename_table("category_label", "categorylabel"))
        except Exception:
            pass

################################## MARK: CREATE
    def create(self, name):
        """ Create new db in the data folder.
            The name of folder containing the new db has a unique id as name (db_dir_name).
        """
        os.makedirs(self.db_dir, exist_ok=True)
        os.makedirs(self.media_dir, exist_ok=True)

        with database:
            database.create_tables([
                Info, Signals, Acf, Bandwidth, CategoryLabel, 
                Category, Documents, Frequency, Location, Mode, Modulation
            ])

            Info.create(
                name=name,
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                version=1,
                editable=1
            )

        self.load()

################################## MARK: STATS
    @property
    def count_signals(self):
        with database:
            return Signals.select().count()


    @property
    def count_docs(self):
        with database:
            return Documents.select().count()


    @property
    def count_images(self):
        with database:
            return Documents.select().where(Documents.type == 'Image').count()


    @property
    def count_audio(self):
        with database:
            return Documents.select().where(Documents.type == 'Audio').count()

################################## MARK: CRUD
    def rename(self, new_name):
        with database:
            Info.update(name=new_name).execute()
        self.name = new_name
    
    def delete_signal(self, sig_id):
        with database:
            Signals.delete().where(Signals.sig_id == sig_id).execute()
        self._select_all_signals()

    def insert_category_label(self, value):
        with database:
            CategoryLabel.create(value=value)
        self._select_all_category_labels()

    def update_category_label(self, clb_id, value):
        with database:
            CategoryLabel.update(value=value).where(CategoryLabel.clb_id == clb_id).execute()
        self._select_all_category_labels()

    def delete_category_label(self, clb_id):
        with database:
            CategoryLabel.delete().where(CategoryLabel.clb_id == clb_id).execute()
        self._select_all_category_labels()

################################## MARK: ==== SIGNAL ====
class ArtemisSIG():
    """ Main class of the object signal
    """
    def __init__(self, database):
        self.db = database
        self._signal = None

        self.sig_id = None
        self.name = None
        self.description = None
        self.url = None
        self.category = None
        self.frequency = None
        self.bandwidth = None
        self.modulation = None
        self.mode = None
        self.location = None
        self.acf = None
        
        self.documents = None
        self.spectrum_path = None
        self.audio_path = None


    def load(self, sig_id):
        self.sig_id = sig_id

        self._signal = Signals.get(Signals.sig_id == self.sig_id)
        
        self._select_signals()
        self._select_category()
        self._select_frequency()
        self._select_bandwidth()
        self._select_modulation()
        self._select_mode()
        self._select_location()
        self._select_acf()
        self.select_documents()


    @property
    def summary(self):
        return {
            'name': self.name,
            'description': self.description,
            'url': self.url,
            'category': self.category,
            'frequency': self.frequency,
            'bandwidth': self.bandwidth,
            'modulation': self.modulation,
            'mode': self.mode,
            'location': self.location,
            'acf': self.acf,
            'spectrum_path': self.spectrum_path,
            'audio_path': self.audio_path,
            'all_category': self.db.all_category_labels
        }

################################## MARK: CRUD > SELECT
    def _select_signals(self):
        
        self.name = self._signal.name
        self.description = self._signal.description
        self.url = self._signal.url


    def _select_category(self):
        query = (Category
                 .select(Category.cat_id, CategoryLabel.clb_id, CategoryLabel.value)
                 .join(CategoryLabel)
                 .where(Category.sig == self._signal))
        
        self.category = [[c.cat_id, c.clb.clb_id, c.clb.value] for c in query]


    def _select_frequency(self):
        query = self._signal.frequencies.order_by(Frequency.value)

        self.frequency = [
            [f.freq_id, f.value, f.description, format_frequency(f.value)] 
            for f in query
        ]


    def _select_bandwidth(self):
        query = self._signal.bandwidths.order_by(Bandwidth.value)
        self.bandwidth = [
            [b.band_id, b.value, b.description, format_frequency(b.value)] 
            for b in query
        ]


    def _select_acf(self):
        self.acf = [[a.acf_id, a.value, a.description] for a in self._signal.acfs]


    def _select_modulation(self):
        self.modulation = [[m.mdl_id, m.value, m.description] for m in self._signal.modulations]


    def _select_mode(self):
        self.mode = [[m.mod_id, m.value, m.description] for m in self._signal.modes]


    def _select_location(self):
        self.location = [[loc.loc_id, loc.value, loc.description] for loc in self._signal.locations]


    def select_documents(self):
        docs = self._signal.documents
        self.documents = [[d.doc_id, d.extension, d.name, d.description, d.type, d.preview] for d in docs]

        default_spectrum = [d for d in docs if d.type == 'Image' and d.preview == 1]
        default_audio = [d for d in docs if d.type == 'Audio' and d.preview == 1]

        if default_spectrum:
            spec = default_spectrum[0]
            default_spectrum_filename = f"{spec.doc_id}.{spec.extension}"
            full_path = self.db.media_dir / default_spectrum_filename
            self.spectrum_path = QUrl.fromLocalFile(str(full_path.resolve()))
        else:
            self.spectrum_path = 'qrc:///data/images/spectrum_not_available.svg'

        if default_audio:
            aud = default_audio[0]
            default_audio_filename = f"{aud.doc_id}.{aud.extension}"
            full_path = self.db.media_dir / default_audio_filename
            self.audio_path = QUrl.fromLocalFile(str(full_path.resolve()))
        else:
            self.audio_path = ''

################################## MARK: CRUD > UPDATE
    def update_signal(self, sig_id, value, description):
        Signals.update(name=value, description=description).where(Signals.sig_id == sig_id).execute()


    def update_frequency(self, freq_id, value, description):
        Frequency.update(value=value, description=description).where(Frequency.freq_id == freq_id).execute()


    def update_bandwidth(self, band_id, value, description):
        Bandwidth.update(value=value, description=description).where(Bandwidth.band_id == band_id).execute()


    def update_modulation(self, modu_id, value, description):
        Modulation.update(value=value, description=description).where(Modulation.mdl_id == modu_id).execute()


    def update_mode(self, mode_id, value, description):
        Mode.update(value=value, description=description).where(Mode.mod_id == mode_id).execute()


    def update_acf(self, acf_id, value, description):
        Acf.update(value=value, description=description).where(Acf.acf_id == acf_id).execute()


    def update_location(self, loc_id, value, description):
        Location.update(value=value, description=description).where(Location.loc_id == loc_id).execute()


    def update_documents(self, doc_id, name, description, type, is_preview):
        Documents.update(
            name=name, 
            description=description, 
            type=type, 
            preview=is_preview
        ).where(Documents.doc_id == doc_id).execute()

################################## MARK: CRUD > INSERT
    def insert_signal(self, value, description):
        # Returns the created object, if necessary
        return Signals.create(name=value, description=description)


    def insert_frequency(self, value, description):
        Frequency.create(sig=self.sig_id, value=value, description=description)


    def insert_bandwidth(self, value, description):
        Bandwidth.create(sig=self.sig_id, value=value, description=description)


    def insert_modulation(self, value, description):
        Modulation.create(sig=self.sig_id, value=value, description=description)


    def insert_mode(self, value, description):
        Mode.create(sig=self.sig_id, value=value, description=description)


    def insert_acf(self, value, description):
        Acf.create(sig=self.sig_id, value=value, description=description)


    def insert_location(self, value, description):
        Location.create(sig=self.sig_id, value=value, description=description)


    def insert_category(self, clb_id):
        Category.create(sig=self.sig_id, clb=clb_id)


    def insert_document(self, doc_lst):
        new_doc = Documents.create(
            sig=self.sig_id,
            name=doc_lst[2],
            description=doc_lst[3],
            extension=doc_lst[1],
            type=doc_lst[4],
            preview=doc_lst[5]
        )
        return new_doc.doc_id

################################## MARK: CRUD > DELETE
    def delete_signal(self):
        Signals.delete().where(Signals.sig_id == self.sig_id).execute()


    def delete_frequency(self, freq_id):
        Frequency.delete().where(Frequency.freq_id == freq_id).execute()


    def delete_bandwidth(self, band_id):
        Bandwidth.delete().where(Bandwidth.band_id == band_id).execute()


    def delete_modulation(self, modu_id):
        Modulation.delete().where(Modulation.mdl_id == modu_id).execute()


    def delete_mode(self, mode_id):
        Mode.delete().where(Mode.mod_id == mode_id).execute()


    def delete_acf(self, acf_id):
        Acf.delete().where(Acf.acf_id == acf_id).execute()


    def delete_location(self, loc_id):
        Location.delete().where(Location.loc_id == loc_id).execute()


    def delete_document(self, doc_id):
        Documents.delete().where(Documents.doc_id == doc_id).execute()


    def delete_category(self, cat_id):
        Category.delete().where(Category.cat_id == cat_id).execute()
