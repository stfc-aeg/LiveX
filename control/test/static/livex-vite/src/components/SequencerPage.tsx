import { OdinSequencer } from 'odin-sequencer-ui';

// This page acts as a 'wrapper' for the odinsequencer to prevent endpoints causing rerenders of all
// App.jsx children needlessly.
interface SequencerPageProps {
  endpoint_url: string;
}

function SequencerPage(props: SequencerPageProps) {
    const {endpoint_url} = props;

    return (
      <OdinSequencer endpoint_name={'sequencer'} endpoint_url={endpoint_url} poll_interval={1000}/>
    )
}

export default SequencerPage;


