import React from 'react';
import { useState, useEffect } from 'react';
import Col from 'react-bootstrap/Col';
import { Container } from 'react-bootstrap';
import Row from 'react-bootstrap/Row';
import Button from 'react-bootstrap/Button';
import { OdinGraph, TitleCard } from 'odin-react';
import InputGroup from 'react-bootstrap/InputGroup';

// This component, for convenience, assumes the data is in a `monitor/<name>` structure in the
// ParameterTree. This makes it easy to edit but a little bit dumb.
function MonitorGraph(props) {
    const {endpoint, title, seriesData} = props;

    const [data, setData] = useState([]);
    const [seriesNames, setSeriesNames] = useState([]);
  
    // Initialise enabled traces outside of useEffect, all to true
    const [enabledTraces, setEnabledTraces] = useState(() =>
      seriesData.reduce((accum, {seriesName}, index) => {
        accum[index] = true;
        return accum;
      }, {})
    ); // Which traces should be shown

    useEffect(() => {
      // Map props data out to be returned in array form
      const allData = seriesData.map(({dataPath, param}) => {
        let keys = dataPath.split("/");
        let dataA = keys.reduce((accum,key) => accum?.[key], endpoint?.data);

        // Ensure dataA[param] exists to avoid errors
        return dataA?.[param] !== undefined ? [dataA?.[param]] : [];
      });
      const legendData = seriesData.map(({seriesName}) => {
        return seriesName;
      })

      // Flatten this (just in case) and set it to be the graph data
      setData(allData.flat());
      setSeriesNames(legendData.flat());
    }, [endpoint.data, seriesData]);

    const toggleTrace = (index) => {
      setEnabledTraces((prev) => ({
        ...prev, // Same data as before in new object
        [index]: !prev[index] // Toggle the previous value at that index
      }));
    };

    // Filter the data based on the 
    const filteredData = data.filter((_, index) => enabledTraces[index]);
    const filteredSeriesNames = seriesNames.filter((_, index) => enabledTraces[index]);

    return (
        <Container>
          <Col>
            <TitleCard title={title}>
              <Container>
                <Row>
                  <Col style={{flexDirection: 'row', justifyContent: 'flex-end'}}>
                    <InputGroup>
                      <InputGroup.Text>
                        Toggle Traces
                      </InputGroup.Text>
                      {seriesNames.map((name, index) => (
                        <Button
                          key={index}
                          variant={enabledTraces[index] ? 'outline-secondary' : 'outline-primary'}
                          onClick={() => toggleTrace(index)}>
                            {enabledTraces[index] ? `Disable ${name}` : `Enable ${name}`}
                        </Button>
                      ))}
                    </InputGroup>
                  </Col>
                </Row>
                <Row>
                  <OdinGraph
                    prop_data={filteredData}
                    series_names={filteredSeriesNames}>
                  </OdinGraph>
                </Row>

              </Container>
            </TitleCard>
          </Col>
        </Container>
    )
}

export default MonitorGraph;