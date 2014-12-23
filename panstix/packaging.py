import logging

import lxml

import maec.package.malware_subject
import stix.extensions.malware.maec_4_1_malware
import stix.ttp
import cybox.core
import stix.indicator

from .exceptions import PanStixError
from . import wf

def get_stix_package_from_wfreport(**kwargs):
    # get malware subject from wf submodule
    subargs = {k: v for k,v in kwargs.iteritems() if k in ['hash', 'tag', 'debug', 'report', 'pcap']}
    ms = wf.get_malware_subject_from_report(**subargs)
    hash = ms.malware_instance_object_attributes.properties.hashes.sha256

    # put it in a malwaresubjectlist
    msl = maec.package.malware_subject.MalwareSubjectList()
    msl.append(ms)

    maecpackage = maec.package.package.Package()
    maecpackage.add_malware_subject(ms)

    # create TTP
    mi = stix.extensions.malware.maec_4_1_malware.MAECInstance(maecpackage)
    ttp = stix.ttp.TTP(title="%s"%hash, description="Sample "+hash+" Artifacts and Characterization")
    mb = stix.ttp.behavior.Behavior()
    mb.add_malware_instance(mi)
    ttp.behavior = mb

    # add TTP to STIX package
    stix_package = stix.core.STIXPackage()
    stix_header = stix.core.STIXHeader(description="Sample "+hash+" Artifacts and Characterization", title=hash)
    stix_package.stix_header = stix_header
    stix_package.add_ttp(ttp)

    # and then add sample
    if 'sample' in kwargs:
        s = kwargs['sample']
        samplerao = None
        if s == 'network':
            if not 'debug' in kwargs or \
                not 'tag' in kwargs:
                raise PanStixError('sample from network, but no debug or tag specified')
            samplerao = wf.sample.get_raw_artifact_from_sample_hash(kwargs['tag'], hash, kwargs['debug'])
        elif isinstance(s, basestring):
            f = open(s, "rb")
            sample = f.read()
            f.close()
            samplerao = wf.sample.get_raw_artifact_from_sample(sample)

        if samplerao is not None:
            i = stix.indicator.Indicator(title="Wildfire sample "+hash)
            o = cybox.core.Observable(description="Raw artifact object of wildfire sample "+hash, title="File "+hash)
            o.object_ = samplerao
            i.add_observable(o)
            i.add_indicated_ttp(stix.ttp.TTP(idref=ttp.id_))
            stix_package.add_indicator(i)

    return stix_package
