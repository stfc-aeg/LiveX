import type { SequencerEndpointTypes } from '../EndpointTypes';
import { useAdapterEndpoint } from 'odin-react';
import { OdinSequencer } from 'odin-sequencer-react-ui';

// This page acts as a 'wrapper' for the odinsequencer to prevent endpoints causing rerenders of all
// App.jsx children needlessly.
interface SequencerPageProps {
  endpoint_url: string;
}

function SequencerPage(props: SequencerPageProps) {
    const {endpoint_url} = props;

    const sequencerEndpoint = useAdapterEndpoint<SequencerEndpointTypes>('sequencer', endpoint_url, 1000);

    return (
      <OdinSequencer endpoint={sequencerEndpoint}/>
    )
}

export default SequencerPage;


