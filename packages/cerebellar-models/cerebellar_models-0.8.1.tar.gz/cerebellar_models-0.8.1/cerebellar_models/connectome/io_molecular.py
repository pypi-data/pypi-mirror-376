"""
Module for the configuration node of the IO to molecular layer interneurons (MLI) ConnectionStrategy
"""

import numpy as np
from bsb import ConfigurationError, ConnectionStrategy, config, refs
from bsb.mixins import NotParallel


@config.node
class ConnectomeIO_MLI(NotParallel, ConnectionStrategy):
    """
    BSB Connection strategy to connect IO cells to molecular layer interneurons (MLI) cells through PC.
    IO cells which are connected to a PC should also connect to all the MLIs connected to this PC.
    """

    io_pc_connectivity = config.reflist(refs.connectivity_ref, required=True)
    """Connection Strategy that links IO to PC."""
    mli_pc_connectivity = config.reflist(refs.connectivity_ref, required=True)
    """List of Connection Strategies that links MLI to PC."""
    pre_cell_pc = config.ref(refs.cell_type_ref, required=True)
    """Celltype used for to represent PC."""
    depends_on: list[ConnectionStrategy] = config.reflist(refs.connectivity_ref)

    @config.property
    def depends_on(self):
        # Get the possibly missing `_depends_on` list.
        deps = getattr(self, "_depends_on", None) or []
        # Strat is required, but depends on a reference that isn't available when the config loads.
        strat_io = getattr(self, "io_pc_connectivity", None)
        strat_mli = getattr(self, "mli_pc_connectivity", None)
        return [*{*deps, *strat_io, *strat_mli}]

    @depends_on.setter
    def depends_on(self, value):
        self._depends_on = value

    def _assert_dependencies(self):
        # assert dependency rule corresponds to expected ones
        found_post = np.full(len(self.postsynaptic.cell_types), False)
        for strat in self.mli_pc_connectivity:
            post_ct = strat.postsynaptic.cell_types
            if len(post_ct) != 1 or post_ct[0] != self.pre_cell_pc:
                raise ConfigurationError(
                    f"PC cell type of the MLI to PC dependency rule does not correspond "
                    f"to the provided PC type for strat {strat.name}"
                )
            for i, post_ct in enumerate(self.postsynaptic.cell_types):
                if not found_post[i] and post_ct in strat.presynaptic.cell_types:
                    found_post[i] = True
        if not np.all(found_post):
            not_found = np.array([post_ct.name for post_ct in self.postsynaptic.cell_types])[
                ~found_post
            ]
            raise ConfigurationError(
                f"Postsynaptic cells: {not_found} "
                f"is not in any connection set of the MLI to PC dependency rules"
            )
        for strat in self.io_pc_connectivity:
            post_ct = strat.postsynaptic.cell_types
            if len(post_ct) != 1 or post_ct[0] != self.pre_cell_pc:
                raise ConfigurationError(
                    f"PC cell type of the IO to PC dependency rule does not correspond "
                    f"to the provided PC type for strategy {strat.name}"
                )
            for pre_ct in self.presynaptic.cell_types:
                if pre_ct not in strat.presynaptic.cell_types:
                    raise ConfigurationError(
                        f"Presynaptic cell: {pre_ct.name} is not in any connection set of "
                        f"the IO to PC dependency rule {strat.name}"
                    )

    def boot(self):
        self._assert_dependencies()

    def load_connectivity_set(self, connection_strat, cell_type):
        """
        Load the connection locations from a connection strategy that connects the provided cell type to PC.

        :param bsb.connectivity.strategy.ConnectionStrategy connection_strat: Connection strategy to load.
        :param str cell_type: Presynaptic cell type name.
        :return: A tuple containing:
                - an array of the presynaptic cell_type connection locations,
                - an array of the postsynaptic pc connection locations
        """
        cs = connection_strat.get_output_names(cell_type, self.pre_cell_pc)
        assert (
            len(cs) == 1
        ), f"Only one connection set should be given from {connection_strat.name}."
        cs = self.scaffold.get_connectivity_set(cs[0])
        return cs.load_connections().as_globals().all()

    def load_hemitype_connections(self, strategies, hemitype):
        """
        Load the connection locations for all the MLI to PC strategies.
        Will only keep one connection location information for each unique pair of MLI-PC.

        :param list[bsb.connectivity.strategy.ConnectionStrategy] strategies: Connection
         strategies to load.
        :param bsb.connectivity.strategy.HemitypeCollection hemitype: Hemitype
        :return: A tuple containing:
                - an array of the presynaptic connection locations
                - an array of the postsynaptic connection locations
                - an array of the placement set indexes
        """
        loc_all_pre = []
        loc_all_post = []
        ct_ps_ids = []
        # For each hemitype placement set
        for i, ps in enumerate(hemitype.placement):
            for strat in strategies:
                try:
                    # Fetch the corresponding connectivity set info if it exists
                    loc_pre, loc_post = self.load_connectivity_set(strat, ps.cell_type)
                except ValueError:
                    continue
                # keep one unique pair of mli to pc
                to_keep = np.unique(
                    np.concatenate([[loc_pre[:, 0]], [loc_post[:, 0]]]).T,
                    axis=0,
                    return_index=True,
                )[1]
                loc_all_pre.extend(loc_pre[to_keep])
                loc_all_post.extend(loc_post[to_keep])
                ct_ps_ids.extend(np.repeat(i, len(to_keep)))

        return np.asarray(loc_all_pre), np.asarray(loc_all_post), np.asarray(ct_ps_ids)

    def connect(self, pre, post):
        # We retrieve the connectivity data for the mli-pc connectivity and io-pc connectivity
        loc_io, loc_pc, ct_io_ids = self.load_hemitype_connections(self.io_pc_connectivity, pre)
        loc_mli, loc_mli_pc, ct_mli_ids = self.load_hemitype_connections(
            self.mli_pc_connectivity, post
        )

        for j, pre_ps in enumerate(pre.placement):
            loc_pc = loc_pc[:, 0][ct_io_ids == j]
            u_purkinje = np.unique(loc_pc)
            io_pc_list = []
            mli_per_pc_list = []
            grouped_ps_ids = []
            for current in u_purkinje:
                io_pc_list.append(loc_io[loc_pc == current][:, 0])
                mli_ids = loc_mli_pc[:, 0] == current
                mli_per_pc_list.append(loc_mli[mli_ids][:, 0])
                grouped_ps_ids.append(ct_mli_ids[mli_ids])

            max_len = np.max(
                [
                    [len(mli_ids), len(io_ids)]
                    for mli_ids, io_ids in zip(mli_per_pc_list, io_pc_list)
                ],
                axis=0,
            )
            max_connections = np.prod(max_len) * u_purkinje.size
            pre_locs = np.full((max_connections, 3), -1, dtype=int)
            post_locs = np.full((max_connections, 3), -1, dtype=int)
            ps_locs = np.full(max_connections, -1, dtype=int)
            ptr = 0
            for i, io_ids in enumerate(io_pc_list):
                ln = len(mli_per_pc_list[i])
                for current in io_ids:
                    pre_locs[ptr : ptr + ln, 0] = current
                    post_locs[ptr : ptr + ln, 0] = mli_per_pc_list[i]
                    ps_locs[ptr : ptr + ln] = grouped_ps_ids[i]
                    ptr = ptr + ln

            # because we are using global indices we need to extract the global ps
            for i, post_ps in enumerate(post.placement):
                post_ps = self.scaffold.get_placement_set(post_ps.cell_type)
                current = (ps_locs == i)[:ptr]
                self.connect_cells(
                    pre_ps, post_ps, pre_locs[:ptr][current], post_locs[:ptr][current]
                )
