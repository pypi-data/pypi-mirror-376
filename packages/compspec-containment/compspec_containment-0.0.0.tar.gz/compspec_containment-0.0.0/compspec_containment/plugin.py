import argparse
import logging
import sys

from compspec.create.jsongraph import JsonGraph
from compspec.plugin import PluginBase

import compspec_containment.defaults as defaults

logger = logging.getLogger("compspec-containment")

try:
    import flux
    import flux.kvs
    from fluxion.resourcegraph.V1 import FluxionResourceGraphV1
except ImportError:
    sys.exit("Cannot import 'flux'. Please run extraction from a Flux instance.")


class ContainmentGraph(JsonGraph):
    pass


class Plugin(PluginBase):
    """
    The containment subsystem extractor plugin
    """

    # These metadata fields are required (and checked for)
    description = "containment subsystem"
    namespace = defaults.namespace
    version = defaults.spec_version
    plugin_type = "generic"

    def add_arguments(self, subparser):
        """
        Add arguments for the plugin to show up in argparse
        """
        plugin = subparser.add_parser(
            self.name,
            formatter_class=argparse.RawTextHelpFormatter,
            description=self.description,
        )
        # Ensure these are namespaced to your plugin
        plugin.add_argument(
            "cluster",
            help="Cluster name for top level of graph",
        )

    def extract(self, args, extra):
        """
        Search a spack install for installed software
        """

        # Create the containment graph
        g = ContainmentGraph("cluster")
        g.metadata["type"] = "containment"
        g.metadata["name"] = args.cluster
        g.metadata["install_name"] = args.name

        # The root node is the cluster, although we don't use it from here"
        g.generate_root()

        # Get the R-lite spec to convert to JGF.
        handle = flux.Flux()
        rlite = flux.kvs.get(handle, "resource.R")
        jgf = FluxionResourceGraphV1(rlite)
        jgf.set_metadata(g.metadata)

        # Generate a dictionary with custom metadata
        return jgf.to_JSON()
