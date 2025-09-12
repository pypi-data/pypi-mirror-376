# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import math
import threading
from collections import defaultdict

from odoo import api, fields, models, tools
from odoo.osv.expression import AND, OR, expression

from ..exceptions import (
    NoPickingCandidateError,
    NoSuitableDeviceError,
    PickingCandidateNumberLineExceedError,
    PickingSplitNotPossibleError,
)


class MakePickingBatch(models.TransientModel):
    _name = "make.picking.batch"
    _description = "Make a batch picking wizard"

    picking_type_ids = fields.Many2many(
        comodel_name="stock.picking.type",
        relation="make_picking_batch_picking_type_rel",
        column1="batch_id",
        column2="picking_type_id",
        string="Default operation types",
        help="Default list of eligible operation types when creating a batch transfer",
    )
    stock_device_type_ids = fields.Many2many(
        comodel_name="stock.device.type",
        relation="make_picking_batch_device_type_rel",
        column1="batch_id",
        column2="device_type_id",
        string="Default device types",
        help="Default list of eligible device types when creating a batch transfer",
    )
    user_id = fields.Many2one(
        "res.users", string="Responsible", default=lambda self: self.env.user
    )
    maximum_number_of_preparation_lines = fields.Integer(
        default=20,
        string="Maximum number of preparation lines for the batch",
        required=True,
    )
    group_pickings_by_partner = fields.Boolean(
        default=False,
        string="Group pickings by partner",
        help="All the pickings related to one partner will be put into the same bins",
    )
    restrict_to_same_priority = fields.Boolean(
        default=False,
        string="Restrict to the same priority",
        help="Only the pickings with the same priority will be selected "
        "for this batch.",
    )
    restrict_to_same_partner = fields.Boolean(
        default=False,
        string="Restrict to the same partner",
        help="Only the pickings with the same partner will be selected for this batch.",
    )
    picking_locking_mode = fields.Selection(
        selection=[
            ("sql_for_update_skip_locked", "SQL FOR UPDATE SKIP LOCKED"),
        ],
        default=lambda self: self._get_default_picking_locking_mode(),
        string="Picking locking mode",
        help="Define the way the system will search and lock the pickings. "
        "In the same time, picking already locked by another transaction will "
        "be skipped. This should reduce the risk of deadlocks if 2 users "
        "try to create a batch at the same time.",
    )
    add_picking_list_in_error = fields.Boolean(
        default=False,
        string="Add all the names of the pickings in error message",
        help="If not suitable device is provided for the pickings candidates, "
        "the error message will contain the list of the pickings names. In some"
        "cases, this list can be very long. That's why this option is unchecked"
        "by default.",
    )

    split_picking_exceeding_limits = fields.Boolean(
        default=False,
        string="Split pickings exceeding limits",
        help="If checked, the pickings exceeding the maximum number of lines, "
        "volume or weight of available devices will be split into multiple pickings "
        "to respect the limits. If unchecked, the pickings exceeding the limits will "
        "not be added to the batch. The limits are defined by the limits of the last "
        "available devices.",
    )

    __slots__ = (
        "_volume_by_partners",
        "_device",
        "_remaining_weight",
        "_remaining_nbr_picking_lines",
        "_selected_picking_ids",
        "_first_picking",
        "_remaining_nbr_bins",
        "_previous_selected_picking",
    )

    def __init__(self, env, ids=(), prefetch_ids=()):
        super().__init__(env, ids=ids, prefetch_ids=prefetch_ids)
        self._reset_counters()

    @api.model
    def _get_default_picking_locking_mode(self):
        # in test mode we don't use a locking mode by default to avoid
        # to collide with the test transaction
        if self.env.registry.in_test_mode() or getattr(
            threading.current_thread(), "testing", False
        ):
            return None
        return "sql_for_update_skip_locked"

    def create_batch(self) -> dict:
        self.ensure_one()
        batch = self._create_batch(raise_if_not_possible=True)
        action = {
            "type": "ir.actions.act_window",
            "name": batch.name,
            "res_model": "stock.picking.batch",
            "res_id": batch.id,
            "view_mode": "form",
            "target": "current",
        }
        return action

    def _reset_counters(self):
        self._volume_by_partners = defaultdict(lambda: 0)
        self._device = None
        self._remaining_weight = None  # None means unlimited
        self._remaining_nbr_picking_lines = 0
        self._selected_picking_ids = []
        self._first_picking = None
        self._remaining_nbr_bins = None
        self._previous_selected_picking = None

    def _get_picking_order_by(self):
        self.ensure_one()
        # we try to process first the pickings assigned to the user
        # then the pickings which are not assigned to any user
        # IN postgres, NULL values values sort as if larger than any non-null value;
        # that is, NULLS FIRST is the default for DESC order, and NULLS LAST otherwise
        # https://www.postgresql.org/docs/current/queries-order.html
        # so we need to sort user_id asc to have NULLS LAST
        if self.group_pickings_by_partner:
            return (
                "user_id asc, priority desc, scheduled_date asc, "
                "partner_id desc, id asc"
            )
        return "user_id asc, priority desc, scheduled_date asc, id asc"

    def _get_picking_domain_common(self):
        domain = [
            ("state", "in", ("partially_available", "assigned")),
            ("batch_id", "=", False),
            ("user_id", "in", [self.user_id.id, False] if self.user_id else [False]),
        ]
        return domain

    def _get_picking_domain_for_first(self, no_nbr_lines_limit=False):
        picking_domain_common = self._get_picking_domain_common()
        apply_limit_on_nbr_lines = not no_nbr_lines_limit
        picking_domain_first = [
            ("picking_type_id", "in", self.picking_type_ids.ids),
        ]
        if apply_limit_on_nbr_lines:
            picking_domain_first.append(
                (
                    "nbr_picking_lines",
                    "<=",
                    self.maximum_number_of_preparation_lines,
                )
            )
        return AND([picking_domain_common, picking_domain_first])

    def _get_picking_domain_for_device(self, device):
        domain = []
        if device.min_volume:
            domain.append(("volume", ">=", device.min_volume))
        if device.max_volume:
            domain.append(("volume", "<=", device.max_volume))
        if device.max_weight:
            domain.append(("weight", "<=", device.max_weight))
        return domain

    def _get_picking_domain_for_additional(self):
        """Provides the domain expressing the additional constraints to apply to
        get the next picking to add to the batch.
        """
        excluded_ids = self._selected_picking_ids
        domain = [
            (
                "nbr_picking_lines",
                "<=",
                self._remaining_nbr_picking_lines,
            ),
            ("id", "not in", excluded_ids),
            ("picking_type_id", "=", self._first_picking.picking_type_id.id),
        ]
        if self._remaining_weight is not None:  # None means unlimited
            domain.append(("weight", "<=", self._remaining_weight))
        previous_picking = self._previous_selected_picking
        if self.restrict_to_same_priority:
            domain.append(("priority", "=", previous_picking.priority))
        if self.restrict_to_same_partner:
            domain.append(("partner_id", "=", previous_picking.partner_id.id))
        volume_domains = [
            [
                ("volume", "<=", self._get_remaining_volume()),
            ]
        ]
        if self.group_pickings_by_partner:
            # in case of grouping by partner, we allow to group picking into
            # the same bins. That means that the volume available for the
            # partner does not depend on the volume of remaining bins only
            # but also on the remaining volume into the bins already used by
            # the partner. Since results are sorted by partner, the search
            # takes as partner the partner of the previous picking.
            previous_partner = previous_picking.partner_id
            volume_domains.append(
                [
                    ("partner_id", "=", previous_partner.id),
                    (
                        "volume",
                        "<=",
                        self._get_remaining_volume(previous_partner),
                    ),
                ]
            )
        return AND([domain, OR(volume_domains)])

    def _execute_search_pickings(self, domain, limit=None):
        """Hook to allow to override the search of pickings

        :param domain: domain to search pickings
        :param limit: number of pickings to search

        :return: recordset of pickings
        """
        if self.picking_locking_mode == "sql_for_update_skip_locked":
            # we all transform our domain expression into a raw sql expression
            # to be able to use the FOR UPDATE NO WAIT clause
            # we use the same order as the orm to be sure to have the same result
            # as the orm
            Picking = self.env["stock.picking"]
            query = expression(domain, Picking).query
            Picking._apply_ir_rules(query, "read")
            query.order = self._get_picking_order_by()
            if limit:
                query.limit = limit
            query_str, params = query.select("id")
            query_str = f"{query_str} FOR UPDATE SKIP LOCKED"
            self.env.cr.execute(query_str, params)
            picking_ids = [row[0] for row in self.env.cr.fetchall()]
            return self.env["stock.picking"].browse(picking_ids)

        return self.env["stock.picking"].search(
            domain, order=self._get_picking_order_by(), limit=limit
        )

    def _split_first_picking_for_limit(self, picking):
        last_device = self.stock_device_type_ids[-1]
        if last_device.split_mode == "dimension":
            return (
                self.env["stock.split.picking"]
                .with_context(active_ids=picking.ids)
                .create(
                    {
                        "mode": "dimensions",
                        "max_nbr_lines": self.maximum_number_of_preparation_lines,
                        "max_volume": last_device.max_volume,
                        "max_weight": last_device.max_weight,
                    }
                )
                ._action_apply()
            )

    def _is_picking_exceeding_limits(self, picking):
        """Check if the picking exceeds the limits of the available devices.

        :param picking: the picking to check
        """
        # First check the number of lines
        if (
            self.maximum_number_of_preparation_lines
            and picking.nbr_picking_lines > self.maximum_number_of_preparation_lines
        ):
            return True
        # Then, check the device limits
        last_device = self.stock_device_type_ids[-1]
        if last_device.split_mode == "dimension":
            if last_device.max_volume and picking.volume > last_device.max_volume:
                return True
            if last_device.max_weight and picking.weight > last_device.max_weight:
                return True
        return False

    def _get_first_picking(self, raise_if_not_found=False):
        """Get the first picking to add to the batch.

        If the split_picking_exceeding_limits is set, we try to find the first picking
        without taking into account the limit on the number of lines and we split it
        if it exceeds the limits. If the split is not possible, we raise an error.

        Otherwise, we try to find the first picking taking into account the limit on the
        number of lines.
        """
        no_limit = self.split_picking_exceeding_limits
        domain = self._get_picking_domain_for_first(no_nbr_lines_limit=no_limit)
        if not no_limit:
            device_domains = []
            for device in self.stock_device_type_ids:
                device_domains.append(self._get_picking_domain_for_device(device))
            domain = AND([domain, OR(device_domains)])
        picking = self._execute_search_pickings(domain, limit=1)
        if not picking and not no_limit and raise_if_not_found:
            self._raise_create_batch_not_possible()
        # at this stage we have the first picking to add to the batch but it could
        # exceed the limits of the available devices. In this case we split the
        # picking and return the picking to add to the batch. The split is done only
        # if the split_picking_exceeding_limits is set to True.
        if (
            picking
            and self.split_picking_exceeding_limits
            and self._is_picking_exceeding_limits(picking)
        ):
            split_picking = self._split_first_picking_for_limit(picking)
            if not split_picking and raise_if_not_found:
                raise PickingSplitNotPossibleError(picking)
            picking = split_picking
        return picking

    def _get_additional_picking(self):
        """Get the next picking to add to the batch."""
        domain = self._get_picking_domain_for_additional()
        domain = AND([domain, self._get_picking_domain_common()])
        return self._execute_search_pickings(domain, limit=1)

    def _get_remaining_volume(self, partner=False):
        """Get the remaining volume for the current device according to the
        number of free bins.

        :param partner: if set, the remaining volume will add to the volume available
        if free bins the volume remaining in the bins already used by the partner
        """
        remaining_volume = self._remaining_nbr_bins * self._device.volume_per_bin
        if partner and self._device.volume_per_bin:
            # for a partner we must take into account the remaining volume in
            # bins already used by the partner and the volume of the remaining
            # bins
            partner_volume = self._volume_by_partners[partner.id]
            partner_nbr_bins_used = math.ceil(
                partner_volume / self._device.volume_per_bin
            )
            partner_remaining_volume_in_bins = (
                partner_nbr_bins_used * self._device.volume_per_bin
            ) - partner_volume
            remaining_volume += partner_remaining_volume_in_bins
        return remaining_volume

    def _compute_device_to_use(self, picking):
        for device in self.stock_device_type_ids.sorted("sequence"):
            if picking.filtered_domain(self._get_picking_domain_for_device(device)):
                return device
        return self.env["stock.device.type"]

    def _volume_condition_for_device_choice(
        self, min_volume, picking_volume, max_volume
    ):
        lower_bound = tools.float_compare(picking_volume, min_volume, 2) >= 0
        upper_bound = tools.float_compare(max_volume, picking_volume, 2) >= 0
        return lower_bound and upper_bound

    def _raise_create_batch_not_possible(self):
        """Raise the correct error to desrcibe why it's not possible to
        create a batch."""
        # At this stage we know that there is no picking to process
        # at least for the list of devices. To provide to the user
        # the right information about the reason why there is no picking
        # we check if there is a candidate pickings without device
        # constrains. If not, we raise an error to inform the user that there
        # is no picking to process otherwise we raise an error to inform the
        # user that there is not suitable device to process the pickings.
        domain = self._get_picking_domain_for_first(no_nbr_lines_limit=True)
        device_domains = []
        for device in self.stock_device_type_ids:
            device_domains.append(self._get_picking_domain_for_device(device))
        domain = AND([domain, OR(device_domains)])
        candidates = self.env["stock.picking"].search(domain, limit=1)
        if candidates:
            raise PickingCandidateNumberLineExceedError(
                candidates, self.maximum_number_of_preparation_lines
            )

        domain = self._get_picking_domain_for_first()
        limit = 1
        if self.add_picking_list_in_error:
            limit = None
        candidates = self.env["stock.picking"].search(domain, limit=limit)
        if candidates:
            pickings = (
                candidates if self.add_picking_list_in_error else candidates.browse()
            )
            raise NoSuitableDeviceError(pickings=pickings)
        raise NoPickingCandidateError(self.env)

    def _create_batch(self, raise_if_not_possible=False):
        """Create a batch transfer."""
        self._reset_counters()
        # first we try to get the first picking for the user
        first_picking = self._get_first_picking(
            raise_if_not_found=raise_if_not_possible
        )
        if not first_picking:
            return self.env["stock.picking.batch"].browse()
        device = self._compute_device_to_use(first_picking)
        if not device:
            if raise_if_not_possible:
                raise NoSuitableDeviceError(pickings=first_picking)
            return self.env["stock.picking.batch"].browse()
        self._init_counters(first_picking, device)
        self._apply_limits()
        vals = self._create_batch_values()
        batch = self.env["stock.picking.batch"].create(vals)
        return batch

    def _init_counters(self, first_picking, device):
        """Initialize the counters used to compute the batch.
        This method is called at the beginning of the batch creation. It allows
        to initialize the counters used to filter the pickings to add to the
        batch.

        :param first_picking: the first picking to add to the batch
        :param device: the device to use to prepare the batch
        """
        self._device = device
        self._remaining_weight = (
            max(device.max_weight - first_picking.weight, 0)
            if device.max_weight
            else None  # None means unlimited
        )
        self._remaining_nbr_picking_lines = (
            self.maximum_number_of_preparation_lines - first_picking.nbr_picking_lines
        )
        self._selected_picking_ids = [first_picking.id]
        self._first_picking = first_picking
        nbr_bins = self._get_nbr_bins_for_picking(first_picking)
        self._remaining_nbr_bins = device.nbr_bins - nbr_bins
        self._previous_selected_picking = first_picking

    def _get_nbr_bins_for_picking(self, picking):
        """Get the number of bins used by the picking.
        If the pickings are grouped by partner, we compute the number of new bins
        required to add the picking to the batch. To do so, each time we add a
        picking for a partner, we sum the volume of the current picking to
        the volume of the previous pickings for the same partner stored in
        self._volume_by_partners. (the self._volume_by_partners is updated
        with this new value). The number of bins required to store the new
        picking is the difference between the number of bins required to store
        the previous volume and the number of bins required to store the new
        volume.

        :param picking: picking to get the number of bins
        """
        nbr_bins = picking._get_nbr_bins_for_device(self._device)
        if self.group_pickings_by_partner:
            picking_volume = picking.volume
            if not picking_volume:
                # if a picking has no volume defined we use the volume per bin
                # of the device by convention a picking without volume fill a complete
                # bin
                picking_volume = self._device.volume_per_bin
            if not self._device.volume_per_bin:
                # We should return current result to avoid division per 0
                return nbr_bins
            old_volume = self._volume_by_partners[picking.partner_id]
            new_volume = picking_volume + old_volume
            nbr_bins = math.ceil(new_volume / self._device.volume_per_bin) - math.ceil(
                old_volume / self._device.volume_per_bin
            )
            self._volume_by_partners[picking.partner_id] = new_volume
        return nbr_bins

    def _add_picking(self, picking):
        """Add a picking to the batch.
        At the same time, we update the counters to decrement the remaining
        resources available for the batch.

        :param picking: picking to add to the batch
        """
        self._selected_picking_ids.append(picking.id)
        self._remaining_weight -= picking.weight
        self._remaining_nbr_picking_lines -= picking.nbr_picking_lines
        nbr_bins = self._get_nbr_bins_for_picking(picking)
        self._remaining_nbr_bins -= nbr_bins
        self._previous_selected_picking = picking

    def _apply_limits(self):
        """
        Once we get the first picking and the device to use, we look
        for other pickings to add to the batch. We add pickings as long as the
        conditions are respected.
        """
        picking = self._first_picking
        while picking:
            if self._remaining_nbr_bins == 0:
                break
            picking = self._get_additional_picking()
            if picking:
                self._add_picking(picking)

    def _create_batch_values(self):
        selected_pickings = self.env["stock.picking"].browse(self._selected_picking_ids)
        return {
            "picking_ids": [(6, 0, selected_pickings.ids)],
            "user_id": self.user_id.id,
            "state": "draft",
            "picking_device_id": self._device.id if self._device else None,
            "is_wave": False,
            "batch_weight": sum(selected_pickings.mapped("weight")),
            "batch_volume": sum(selected_pickings.mapped("volume")),
            "batch_nbr_bins": self._device.nbr_bins - self._remaining_nbr_bins,
            "batch_nbr_lines": sum(selected_pickings.mapped("nbr_picking_lines")),
        }
