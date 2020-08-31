# -*- coding: utf-8 -*-
from .traverse import *
from .taximetria import *
from datetime import datetime


def _load(data, sheet_name: str = None):
    if isinstance(data, str):
        _sheet = 0 if sheet_name is None else sheet_name
        return pd.read_excel(data, sheet_name=_sheet)
    return data


def extract_workind_dir(data):
    if isinstance(data, str):
        _path = Path(data)
        return _path if _path.is_dir() else _path.parent
    elif isinstance(data, Path):
        return data if data.is_dir() else data.parent
    else:
        raise IsADirectoryError("""Working directory can't be infered from data.
        Provide 'working_dir' when instantiating the class SurveyProject.""")


def styler(data: pd.DataFrame, formatter: dict):
    return data.style.format(formatter).apply(warning,
                                              subset=['angular', 'horizontal'])


class SurveyProject:
    def __init__(self,
                 name: str = None,
                 traverse_data: (str, pd.DataFrame) = None,
                 sideshot_data: (str, pd.DataFrame) = None,
                 traverses: (str, pd.DataFrame) = None,
                 known_points: (str, pd.DataFrame) = None,
                 working_dir: (str, Path) = None):

        self.name = name
        self.time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        self.working_dir = working_dir if working_dir else extract_workind_dir(
            traverses)

        self.t_data = _load(traverse_data)
        self.s_data = _load(sideshot_data)
        self.t_list = _load(traverses)

        self.stations = Container(_load(known_points))
        self.sideshots = Container()

        self.computed_traverses = []
        self.computed_traverses_count = 0
        self.computed_traverses_info = None

        self.computed_sideshots = []
        self.computed_sideshots_count = 0

    @classmethod
    def from_single_file(cls, file):
        _path = Path(file)
        _name = _path.stem
        _all_data = pd.ExcelFile(_path)
        _traverse_data = _all_data.parse('Traverse_Measurements')
        _sideshot_data = _all_data.parse('Taximetrika')
        _traverses = _all_data.parse('Traverses')
        _known_points = _all_data.parse('Known_Points')
        _working_dir = _path.parent

        return cls(name=_name,
                   traverse_data=_traverse_data,
                   sideshot_data=_sideshot_data,
                   traverses=_traverses,
                   known_points=_known_points,
                   working_dir=_working_dir)

    def point2obj(self, points: (list, tuple)) -> List[Point]:
        return [self.stations[points[0]], self.stations[points[1]]]

    def prepare_data(self):
        self.t_list['stations'] = self.t_list['stations'].str.split('-')

        self.t_list['start'] = self.t_list['stations'].apply(
            lambda x: x[:2])

        self.t_list['last'] = self.t_list['stations'].apply(
            lambda x: x[-2:])

    def compute_traverses(self):
        for traverse in self.t_list.itertuples():
            if traverse.t_type == 'LinkTraverse':
                tr = LinkTraverse(stops=traverse.stations,
                                  data=self.t_data,
                                  start=self.point2obj(traverse.start),
                                  finish=self.point2obj(traverse.last),
                                  working_dir=self.working_dir)
            elif traverse.t_type == 'ClosedTraverse':
                tr = ClosedTraverse(stops=traverse.stations,
                                    data=self.t_data,
                                    start=self.point2obj(traverse.start),
                                    working_dir=self.working_dir)
            else:
                tr = OpenTraverse(stops=traverse.stations,
                                  data=self.t_data,
                                  start=self.point2obj(traverse.start),
                                  working_dir=self.working_dir)

            if tr.is_validated():
                tr.compute()

                self.computed_traverses.append(tr)

                if self.computed_traverses_info is not None:
                    self.computed_traverses_info = \
                        self.computed_traverses_info.append(
                            tr.metrics.copy()).reset_index(drop=True)
                else:
                    self.computed_traverses_info = tr.metrics.copy()

        self.stations = self.stations + sum(
            [trav.stations for trav in self.computed_traverses])

        self.computed_traverses_count = len(self.computed_traverses)

        return styler(self.computed_traverses_info, traverse_formatter)

    def export_traverses(self):
        _out = self.working_dir.joinpath('Project_Traverses.xlsx')
        with pd.ExcelWriter(_out) as writer:
            for i, traverse in enumerate(self.computed_traverses, 1):
                traverse.odeusi.round(4).to_excel(writer,
                                                  index=False,
                                                  sheet_name=str(i))

    def compute_taximetria(self):
        point_groups = self.s_data.groupby(['station', 'bs'])

        for group in point_groups.groups:
            if group in self.stations:
                _data = point_groups.get_group(group)

                ss = Sideshot(_data,
                              self.stations[group[0]],
                              self.stations[group[1]])

                ss.compute()

                self.computed_sideshots.append(ss)

        self.sideshots = sum([s.points for s in self.computed_sideshots])
        self.sideshots.sort()
        self.computed_sideshots_count = len(self.sideshots)

        print(f"[{self.computed_sideshots_count}] points were calculated.")
