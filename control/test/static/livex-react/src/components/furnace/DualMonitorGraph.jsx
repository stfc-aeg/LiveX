import React from 'react';
import { useState, useEffect } from 'react';
import Col from 'react-bootstrap/Col';
import { Container } from 'react-bootstrap';
import Row from 'react-bootstrap/Row';
import { OdinGraph, TitleCard } from 'odin-react';

// This component, for convenience, assumes the data is in a `monitor/<name>` structure in the
// ParameterTree. It also assumes two bits of data to plot. This makes it dumb but easy to edit.
function MonitorGraph(props) {
    const {endpoint, title, seriesNames, seriesData} = props;

    const [data, setData] = useState([]);

    useEffect(() => {
      const allData = seriesData.map(({dataPath, param_a, param_b}) => {
        const dataA = endpoint.data?.monitor?.[dataPath]?.[param_a];
        const dataB = endpoint.data?.monitor?.[dataPath]?.[param_b];
        return [dataA, dataB];
      });

      setData(allData.flat());
    }, [endpoint.data, seriesData]);

    return (
        <Container>
          <Col>
            <TitleCard title={title}>
              <Container>
                <Row>
                  <OdinGraph
                  prop_data={data}
                  series_names={seriesNames}>
                  </OdinGraph>
                </Row>
              </Container>
            </TitleCard>
          </Col>
        </Container>
    )
}

export default MonitorGraph;