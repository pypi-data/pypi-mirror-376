"""The set of reporters define an interface to report plots or tables"""

from engforge.configuration import Configuration, forge
from engforge.typing import Options
from engforge.logging import LoggingMixin
import attrs
import abc

import os, pathlib
import datetime


def path_exist_validator(inst, attr, value):
    if not isinstance(value, str):
        raise ValueError(f"{attr.name} isnt a string")
    if not os.path.exists(value):
        raise FileExistsError(f"{value} does not exist")


# BASE CLASSSES (PLOT + TABLE)
@attrs.define
class Reporter(LoggingMixin):
    """A mixin intended"""

    name: str = attrs.field(default="reporter")

    def check_config(self):
        """a test to see if the reporter should be used"""
        return True

    @classmethod
    def subclasses(cls, out=None):
        """get all reporters of this type"""
        if out is None:
            out = set()

        for scls in cls.__subclasses__():
            out.add(scls)
            scls.subclasses(scls)

    def upload(self, analysis: "Analysis"):
        self.info(f"uploading {analysis.identity} to {self.identity}")
        raise NotImplemented()


# Functionality Mixins
@attrs.define
class TemporalReporterMixin(Reporter):
    """Provide single or periodic keys"""

    # report_mode: Options("single", "daily", "monthly") #choose wisely

    @property
    def report_root(self):
        raise NotImplemented()

    @property
    def date_key(self):
        d = datetime.datetime.utcnow().date()
        return f"{d.year}.{d.month:02}.{d.day:02}"

    @property
    def month_key(self):
        d = datetime.datetime.utcnow().date()
        return f"{d.year}.{d.month:02}"

    @property
    def report_root(self):
        """define your keys!"""
        raise NotImplemented()


@attrs.define
class DiskReporterMixin(TemporalReporterMixin):
    path: str = attrs.field(default=None, validator=path_exist_validator)

    # whats our /report/<key> gonna be
    report_mode = Options("single", "daily", "monthly")

    @property
    def report_root(self):
        if self.report_mode == "single":
            return self.path
        elif self.report_mode == "daily":
            return os.path.join(self.path, self.date_key)
        elif self.report_mode == "monthly":
            return os.path.join(self.path, self.month_key)

        raise ValueError(f"options failed!")

    def ensure_exists(self):
        if not os.path.exists(self.report_root):
            pth = pathlib.Path(self.report_root)
            pth.mkdir(parents=True, exist_ok=True)

    def ensure_path(self, file_path, is_dir=False):
        pth = pathlib.Path(file_path)
        diri = pth if is_dir else pth.parent
        if not diri.exists():
            diri.mkdir(parents=True, exist_ok=True)


# Basic Reporter Types
@attrs.define
class TableReporter(Reporter):
    """A reporter to upload dataframes to a table store"""

    name: str = attrs.field(default="table_reporter")


@attrs.define
class PlotReporter(Reporter):
    """A reporter to upload plots to a file store"""

    name: str = attrs.field(default="plot_reporter")

    # FIXME: make attrs work... layout class conflict
    # ext = Options('png','jpg','gif')
    # ext: str = attrs.field(default='png')
    ext = "png"

    #     def upload(self, analysis):
    #         for figkey, fig in analysis.stored_plots.items():
    #             try:
    #                 filname = os.path.join(self.report_root, f"{figkey}.{self.ext}")
    #                 self.ensure_path(filname)
    #                 self.info(f"saving {figkey} to {filname}")
    #                 fig.savefig(filname)
    #
    #             except Exception as e:
    #                 self.error(e, f"issue showing {figkey}")
    def upload(self, analyis):
        raise NotImplemented(f"plot reporter subclass needs an upload method")


# Table Reporters
@attrs.define
class CSVReporter(TableReporter, DiskReporterMixin):
    name: str = attrs.field(default="CSV")

    def upload(self, analysis: "Analysis"):
        self.info(f"uploading {analysis.identity} to {self.identity}")
        self.ensure_exists()

        system = analysis.system

        # Make System Dataframe
        af = os.path.join(self.report_root, f"system_{system.name}.csv")
        self.ensure_path(af)
        self.info(f"saving system to: {af}")
        system.dataframe.to_csv(af)


#         # Make Analysis Dataframe
#         af = os.path.join(self.report_root, f"analysis_{analysis.name}.csv")
#         self.ensure_path(af)
#         self.info(f"saving analysis to: {af}")
#         analysis.dataframe.to_csv(af)
#
#         for ckey, comp in system.comp_references().items():
#             af = os.path.join(self.report_root, f"{ckey}_{comp.name}.csv")
#             self.ensure_path(af)
#             self.info(f"saving {ckey} to: {af}")
#             comp.dataframe.to_csv(af)


@attrs.define
class ExcelReporter(TableReporter, DiskReporterMixin):
    name: str = attrs.field(default="EXCEL")


@attrs.define
class GsheetsReporter(TableReporter, TemporalReporterMixin):
    name: str = attrs.field(default="GSHEETS")


# @attrs.define
# class SQLReporter(TableReporter):
#     name: str = attrs.field(default="SQL")
#
#
# @attrs.define
# class ArangoReporter(TableReporter):
#     name: str = attrs.field(default="SQL")


# PLOT Reporters
@attrs.define
class DiskPlotReporter(PlotReporter, DiskReporterMixin):
    name: str = attrs.field(default="DrivePlots")

    def upload(self, analysis):
        for figkey, fig in analysis.stored_plots.items():
            try:
                filname = os.path.join(self.report_root, f"{figkey}.{self.ext}")
                self.ensure_path(filname)
                self.info(f"saving {figkey} to {filname}")
                fig.savefig(filname)

            except Exception as e:
                self.error(e, f"issue showing {figkey}")


@attrs.define
class GdriveReporter(PlotReporter, TemporalReporterMixin):
    name: str = attrs.field(default="Gdrive")
    share_drive: str = attrs.field(
        default=None, validator=attrs.validators.instance_of(str)
    )


# TODO: move to analysis
# def split_dataframe_by_colmum(self,df,max_columns=10):
#     df_cols = list(df.columns)
#     if len(df_cols) < max_columns:
#         return [df]
#
#     col_chunks = list(chunks(df_cols,max_columns))
#     dat_chunks = [df[colck].copy() for colck in col_chunks]
#
#     return dat_chunks

# def cleanup_dataframe(self,df,badwords=('min','max')):
#     tl_df = self.static_dataframe
#     to_drop = [cl for cl in tl_df.columns if any([bw in cl.lower() for bw in badwords])]
#     out_df = tl_df.drop(columns=to_drop)
#     return out_df


# @solver_cached
# def variable_dataframe(self):
#     vals = list(zip(*list((self.variable_data_dict.values()))))
#     cols = list((self.variable_data_dict.keys()))
#     if vals:
#         return pandas.DataFrame(data = vals, columns=cols, copy = True)
#     else:
#         return  None
#
# @solver_cached
# def static_dataframe(self):
#     vals = [list((self.static_data_dict.values()))]
#     cols = list((self.static_data_dict.keys()))
#     if vals:
#         return pandas.DataFrame(data = vals, columns=cols, copy = True)
#     else:
#         return None

# Clearance Methods
# table property internal variables
# __store_options = ('csv','excel','gsheets')#,'db','gsheets','excel','json')
# _store_types = None
# _store_level:int = -1

#     @property
#     def table_iterator(self):
#         '''Checks data to see what type of table it is, type 1 is a single row
#         whereas type 2 & 3 have several rows, but type 2 has some values that are singular
#
#         iterates table_type,values,label'''
#
#         if not self.TABLE:
#             return 0,[],[]
#         if len(self.TABLE) <= 1:
#             yield 1,self.TABLE[1],self.data_label
#         else:
#             #wide outerloop over vars
#             for label in set.union(*[set(tuple(row.keys())) for i,row in self.TABLE.items()]):
#                 #inner loop over data
#                 col = [row[label] if label in row else None for inx,row in self.TABLE.items()]
#
#                 if all([isinstance(cvar,TABLE_TYPES) for cvar in col]): #do a type check
#                     if len(set(col)) <= 1: #All Values Are Similar
#                         yield 2, col[0], label #Can assume that first value is equal to all
#                     else:
#                         yield 3, col, label
#
# def recursive_data_structure(self,levels_to_descend = -1, parent_level=0):
#     '''Returns the static and variable data from each configuration to grab defined by the
#     recursive commands input in this function
#
#     data is stored like: output[level]=[{static,variable},{static,variable},...]'''
#
#     output = {}
#
#     for level,conf in self.go_through_configurations(0,levels_to_descend,parent_level):
#         if level in output:
#             output[level].append({'static':conf.static_dataframe,\
#                                     'variable':conf.variable_dataframe,'conf':conf})
#         else:
#             output[level] = [{'static':conf.static_dataframe,\
#                                 'variable':conf.variable_dataframe,\
#                                 'conf':conf}]
#
#     return output

# Multi-Component Table Combination Methods
# @solver_cached
# def static_data_dict(self):
#     '''returns key-value pairs in table that are single valued, all in type 1, some in type 2'''
#
#     output = {}
#     for tab_type,value,label in self.table_iterator:
#         if tab_type == 1:
#             return {l:v for l,v in zip(label,value)}
#         elif tab_type == 2:
#             output[label] = value
#     return output
#
# @solver_cached
# def variable_data_dict(self):
#     '''returns a dictionary of key value pairs where values list is not the same all of type 3 and some of type 2'''
#     output = {}
#     for tab_type,value,label in self.table_iterator:
#         if tab_type == 3:
#             output[label] = value
#     return output
#
#
# #Multi-Component Table Lookups
# @solver_cached
# def toplevel_static(self):
#     out_df = self.cleanup_dataframe( self.static_dataframe )
#     df_list = self.split_dataframe_by_colmum(out_df,self.max_col_width_static)
#
#     return {'conf':self,'dfs':  df_list }
#
# @solver_cached
# def other_static_tables(self):
#     rds = self.recursive_data_structure(self.store_level)
#     output = []
#     for index, components in rds.items():
#         if index > 0:
#             for comp in components:
#                 if comp['static'] is not None:
#                     df_list = self.split_dataframe_by_colmum(comp['static'],self.max_col_width_static)
#                     output.append({'conf':comp['conf'],'dfs': df_list})
#     return output
#
# @solver_cached
# def variable_tables(self):
#     '''Grabs all valid variable dataframes and puts them in a list'''
#     rds = self.recursive_data_structure(self.store_level)
#
#     output = []
#     for index, components in rds.items():
#         for comp in components:
#             if comp['variable'] is not None:
#                 output.append({'conf':comp['conf'],'df':comp['variable']})
#
#     return output
#
# @solver_cached
# def joined_dataframe(self):
#     '''this is a high level data frame with all data that changes in the system'''
#     if self.variable_tables:
#         return pandas.concat([ vt['df'] for vt in list(reversed(self.variable_tables))],axis=1)
#     else:
#         return None
#
# @property
# def complete_dataframe(self):
#     '''this is a high level data frame with all data in the system'''
#
#     rds = self.recursive_data_structure()
#     if rds:
#         dataframes = []
#         stat_dataframes = []
#         for lvl, comps in rds.items():
#             for comp in comps:
#                 df = comp['conf'].dataframe
#                 if not comp['conf'] is self:
#                     nm = comp['conf'].name.lower()
#                     if nm == 'default':
#                         nm = comp['conf'].__class__.__name__.lower()
#                     nm = nm.replace(' ','_')
#                     strv=f'{nm}_'
#                     strv+='{}'
#                 else:
#                     nm = ''
#                     strv='{}'
#                 df.rename(strv.format, axis=1, inplace=True)
#
#                 dataframes.append(df)
#         return pandas.concat(dataframes,join='outer',axis=1)
#
#     else:
#         return None

# Saving & Data Acces Methods
# def get_field_from_table(self,field,check_type=None,check_value:Callable = None):
#     '''Converts Pandas To Numpy Array By Key, also handles poorly formated fields
#     :param check_type: use a type or tuple of types to validate if the field is of type table
#     :param check_value: use a function to check each value to ensure its valid for return, check type take priority'''
#     if self.joined_dataframe is None:
#         return numpy.array([])
#     elif field in self.joined_dataframe:
#         table = self.joined_dataframe[field]
#     elif field.title() in self.joined_dataframe:
#         table = self.joined_dataframe[field.title()]
#     else:
#         raise Exception('No Field Named {}'.format(field))
#
#     #Remove Infinity
#     table = table.replace([numpy.inf, -numpy.inf], numpy.nan)
#
#     if check_type is not None:
#         if all([isinstance(v,check_type) for v in table]):
#             return table.to_numpy(copy=True)
#         return None
#     elif check_value is not None:
#         if all([check_value(v) for v in table]):
#             return table.to_numpy(copy=True)
#         return None
#
#     return table.to_numpy(dtype=float,copy=True)


# Save functionality
# TODO: get me outta hur
#     def save_table(self,dataframe=None,filename=None,meta_tags=None,*args,**kwargs):
#         '''Header method to save the config in many different formats
#         :param meta_tags: a dictionary with headers being column names, and the value as the item to fill that column'''
#         if dataframe is None:
#             dataframe = self.dataframe
#
#         self.info('saving gsheets...')
#
#         if meta_tags is not None and type(meta_tags) is dict:
#             for tag,value in meta_tags.items():
#                 dataframe[tag] = value
#
#
#         for save_format in self.store_types:
#             try:
#                 if save_format == 'csv':
#                     self.save_csv(dataframe,filename,*args,**kwargs)
#                 elif save_format == 'excel':
#                     self.save_excel(dataframe,filename,*args,**kwargs)
#                 elif save_format == 'gsheets':
#                     self.save_gsheets(dataframe,filename,*args,**kwargs)
#             except Exception as e:
#                 self.error(e,'Issue Saving Tables:')

#     def save_csv(self,dataframe,filename=None,*args,**kwargs):
#         if self.TABLE:
#             if filename is None:
#                 filename = '{}.csv'.format(self.filename)
#             if type(filename) is str and not filename.endswith('.csv'):
#                 filename += '.csv'
#             filepath = os.path.join(self.config_path_daily,filename)
#             dataframe.to_csv(path_or_buf=filepath,index=False,*args,**kwargs)
#
#     def save_excel(self,dataframe,filename=None,*args,**kwargs):
#         if self.TABLE:
#             if filename is None:
#                 filename = '{}.xlsx'.format(self.filename)
#             if type(filename) is str and not filename.endswith('.xlsx'):
#                 filename += '.xlsx'
#             filepath = os.path.join(self.config_path_daily,filename)
#             dataframe.to_excel(path_or_buf=filepath,*args,**kwargs)

#     @property
#     def store_level(self):
#         return self._store_level
#
#     @store_level.setter
#     def store_level(self,new_level:int):
#         assert isinstance(new_level,(int))
#         self._store_level = new_level
#
#     @property
#     def store_types(self):
#         if self._store_types is None:
#             self._store_types = [] #initalization
#         return self._store_types

#     @store_types.setter
#     def store_types(self, new_type_or_list):
#         '''If you add a list or iterable, and each value is a valid output option we will assign it
#         otherwise if its a value in the valid options it will be added.
#         '''
#         if isinstance(new_type_or_list,(list,tuple)):
#             assert all([val in self.__store_options for val in new_type_or_list])
#             self._store_types = list(new_type_or_list)
#
#         elif new_type_or_list in self.__store_options:
#              self._store_types.append(new_type_or_list)
#
#         else:
#             self.warning('store types input not valid {}'.format(new_type_or_list))


#     def save_to_worksheet(self,worksheet:'pygsheets.Worksheet'):
#         '''Saves to a gsheets via pygsheets adds static and regular data'''
#
#         title = self.identity.replace('_',' ').title()
#
#         self.info('saving worksheet as {}'.format(title))
#         wksh = worksheet
#
#         wksh.clear()
#
#         #Static data
#         start = pygsheets.Address((2,2))
#
#         tld = self.toplevel_static
#         sdf = tld['dfs']
#
#         cur_index = start + (1,0)
#         for i,df in enumerate(sdf):
#             self.debug('saving dataframe {}'.format(df))
#             wksh.update_value(start.label,self.identity)
#             wksh.cell(start.label).set_text_format('bold',True)
#             wksh.set_dataframe(df,cur_index.label , extend=True)
#             cur_index += (2,0)
#
#         cur_index += (3,0)
#
#         var_index = pygsheets.Address(cur_index.label)
#
#         max_row = 0
#
#         vrt = self.variable_tables
#         self.info('saving {} other static tables'.format(len(vrt)))
#
#         for dfpack in vrt:
#             conf = dfpack['conf']
#             df = dfpack['df']
#             self.debug('saving dataframe {}'.format(df))
#
#             (num_rows,num_cols) = df.shape
#             max_row = max(max_row,num_rows)
#
#             wksh.update_value((var_index-(1,0)).label,conf.classname)
#             wksh.cell((var_index-(1,0)).label).set_text_format('bold',True)
#
#             wksh.set_dataframe(df,start=var_index.label,extend=True)
#
#             var_index += (0,num_cols)
#
#         cur_index += (3+max_row,0)
#
#         ost = self.other_static_tables
#
#         self.info('saving {} other static tables'.format(len(ost)))
#
#         for dfpack in ost:
#             conf = dfpack['conf']
#             sdf = dfpack['dfs']
#
#             wksh.update_value((cur_index-(1,0)).label,conf.identity)
#             wksh.cell((cur_index-(1,0)).label).set_text_format('bold',True)
#
#             for i,df in enumerate(sdf):
#
#                 self.debug('saving {} dataframe {}'.format(conf.identity, df))
#                 wksh.set_dataframe(df,start=cur_index.label ,extend=True)
#                 cur_index += (2,0)
#
#             cur_index += (3,0)


#     def save_gsheets(self,dataframe,filename=None,index=False,*args,**kwargs):
#         '''A function to save the table to google sheets
#         :param filename: the filepath on google drive - be careful!
#         '''
#         with self.drive.context(filepath_root=self.local_sync_path, sync_root=self.cloud_sync_path) as gdrive:
#             with gdrive.rate_limit_manager( self.save_gsheets,6,dataframe,filename=filename,*args,**kwargs) as tdrive:
#
#                 old_sleep = tdrive._sleep_time
#                 tdrive.reset_sleep_time( max(old_sleep,2.5) )
#
#                 gpath = tdrive.sync_path(self.local_sync_path)
#                 self.info(f'saving as gsheets in dir {self.local_sync_path} -> {gpath}')
#                 parent_id = gdrive.get_gpath_id(gpath)
#                 #TODO: delete old file if exists
#                 tdrive.sleep(2*(1+tdrive.time_fuzz*random.random()))
#                 if tdrive and tdrive.gsheets:
#                     sht = tdrive.gsheets.create(filename,folder=parent_id)
#
#                     tdrive.sleep(2*(1+tdrive.time_fuzz*random.random()))
#                     tdrive.cache_directory(parent_id)
#
#                     wk = sht.sheet1
#
#                     wk.rows = dataframe.shape[0]
#                     gdrive.sleep(2*(1+tdrive.time_fuzz*random.random()))
#
#                     wk.set_dataframe(dataframe,start='A1',fit=True)
#                     gdrive.sleep(2*(1+tdrive.time_fuzz*random.random()))
#
#                     #TODO: add in dataframe dict with schema sheename: {dataframe,**other_args}
#                     self.info('gsheet saved -> {}'.format(os.path.join(gpath,filename)))
#
#                 tdrive.reset_sleep_time( old_sleep )
