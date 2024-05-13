import React from 'react';
import { useState, useEffect } from 'react';
import Col from 'react-bootstrap/Col';
import { Container } from 'react-bootstrap';
import Row from 'react-bootstrap/Row';
import { OdinGraph, TitleCard } from 'odin-react';


function TemperatureGraph(props) {
    const {liveXEndPoint} = props;

    const [tempData, changeTempData] = useState([{}]);

    const tempDataA = liveXEndPoint.data.temp_monitor?.temperature_a;
    const tempDataB = liveXEndPoint.data.temp_monitor?.temperature_b;

    // Graph re-renders when data changes
    useEffect(() => {
      changeTempData([tempDataA, tempDataB]);
    }, [liveXEndPoint.data.temp_monitor?.temperature_a, liveXEndPoint.data.temp_monitor?.temperature_b]
    )

    return (
        <Container>
          <Col>
            <TitleCard title="temperature graph">
              <Container>
                <Row>
                  <OdinGraph 
                  prop_data={tempData}
                  series_names={["TC1", "TC2"]}>
                  </OdinGraph>
                </Row>
              </Container>
            </TitleCard>
          </Col>
        </Container>
    )
}

export default TemperatureGraph;