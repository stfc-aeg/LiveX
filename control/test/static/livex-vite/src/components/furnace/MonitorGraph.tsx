import { useState, useMemo } from 'react';
import { Row, Col, Button, InputGroup } from 'react-bootstrap';
import { TitleCard, OdinGraph, AdapterEndpoint } from 'odin-react';
import type { ParamTree, ParamNode } from 'odin-react';
import ResizeableOdinGraph from '../ResizeableOdinGraph';

interface MonitorGraphProps {
  endpoint: AdapterEndpoint;
  title: string;
  paths: string[]; // paths to the data in the endpoint, e.g. "temperature_upper/data"
  seriesNames: string[];
}

function MonitorGraph(props: MonitorGraphProps) {
    const {endpoint, title, paths, seriesNames } = props;

    // Initialise enabled traces outside of useEffect, all to true
    const [enabledTraces, setEnabledTraces] = useState(() =>
      Object.fromEntries(paths.map((_, i) => [i, true]))
    ); // Which traces should be shown

    // Look over endpoint.data and follow the paths down it to get the current data
    const data = useMemo(() => {
      if (!endpoint?.data) return paths.map(() => []); // same length as paths
      return paths.map((path) => {
        const val = path
          .split("/")
          // Narrow acc to paramnode|undefined for typing reasons
          .reduce<ParamTree | undefined>((acc, key) => {
            if (!acc || typeof acc !== 'object' || Array.isArray(acc)) return undefined;
            return (acc as ParamNode)[key];
          }, endpoint.data as ParamNode)
        return Array.isArray(val) ? val : []; // always an array
      });
    }, [paths, endpoint?.data]);

    // Filter out any data or names that aren't enabled at that index
    const filteredData = useMemo(() => 
      data.filter((_, i) => enabledTraces[i]), [data, enabledTraces]);

    const filteredNames = useMemo(() =>
      seriesNames.filter((_, i) => enabledTraces[i]), [seriesNames, enabledTraces]);

    // Copy the previous enabledTraces, flip the value for the specific trace
    const toggleTrace = (i: number) =>
      setEnabledTraces((prev) => ({...prev, [i]: !prev[i]}));

    // console.log(filteredData)

    return (
      <TitleCard title={title}>
        <Col>
          <Row>
            <Col style={{flexDirection: 'row', justifyContent: 'flex-end'}}>
              <InputGroup>
                <InputGroup.Text>
                  Toggle Traces
                </InputGroup.Text>
                {seriesNames.map((name, index) => (
                  <Button
                    key={index}
                    variant={enabledTraces[index] ? 'outline-primary' : 'outline-secondary'}
                    onClick={() => toggleTrace(index)}>
                      {enabledTraces[index] ? `Disable ${name}` : `Enable ${name}`}
                  </Button>
                ))}
              </InputGroup>
            </Col>
          </Row>
          <Row>
            <ResizeableOdinGraph
              prop_data={filteredData}
              series_names={filteredNames}
              width={'99%'}
              responsive={false}
            />
          </Row>
        </Col>
      </TitleCard>
    )
}

export default MonitorGraph;