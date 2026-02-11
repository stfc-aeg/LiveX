import React from 'react';
import { useAdapterEndpoint } from 'odin-react';
import { OdinSequencer } from 'odin-sequencer-react-ui';

// This page acts as a 'wrapper' for the odinsequencer to prevent endpoints causing rerenders of all
// App.jsx children needlessly.
function SequencerPage(props) {
    const {endpoint_url} = props;

    const sequencerEndpoint = useAdapterEndpoint('sequencer', endpoint_url, 1000);

    return (
      <OdinSequencer endpoint={sequencerEndpoint}/>
    )
}

export default SequencerPage;


